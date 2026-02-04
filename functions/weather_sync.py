"""
Firebase Cloud Function to fetch weather data from ETL pipeline and cache in Firestore.

This function:
1. Watches for weather requests in Firestore
2. Fetches data from your Airflow ETL pipeline (PostgreSQL)
3. Calls OpenMeteo API for forecast data
4. Caches results in Firestore
5. Calculates spray suitability windows

Deploy with: firebase deploy --only functions
"""

from firebase_functions import firestore_fn, scheduler_fn
from firebase_admin import initialize_app, firestore
import requests
import psycopg2
from datetime import datetime, timedelta
import os

initialize_app()

# Environment variables
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'postgres')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')

OPENMETEO_API = 'https://api.open-meteo.com/v1/forecast'


def get_current_weather_from_db(latitude: float, longitude: float):
    """Fetch latest weather data from your ETL PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            port=POSTGRES_PORT
        )
        cursor = conn.cursor()
        
        # Get most recent weather data for location
        cursor.execute("""
            SELECT temperature, windspeed, winddirection, weathercode, timestamp
            FROM weather_data
            WHERE latitude = %s AND longitude = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (latitude, longitude))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'temperature': result[0],
                'windSpeed': result[1],
                'windDirection': result[2],
                'weatherCode': result[3],
                'timestamp': result[4]
            }
        return None
    except Exception as e:
        print(f"Error fetching from PostgreSQL: {e}")
        return None


def get_forecast_from_openmeteo(latitude: float, longitude: float):
    """Fetch 7-day forecast from OpenMeteo API."""
    try:
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current_weather': True,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max,weathercode',
            'timezone': 'auto',
            'forecast_days': 7
        }
        
        response = requests.get(OPENMETEO_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching from OpenMeteo: {e}")
        return None


def calculate_spray_windows(forecast_data):
    """Calculate spray suitability for each day."""
    spray_windows = []
    
    if not forecast_data or 'daily' not in forecast_data:
        return spray_windows
    
    daily = forecast_data['daily']
    
    for i in range(len(daily['time'])):
        date = daily['time'][i]
        temp_max = daily['temperature_2m_max'][i]
        temp_min = daily['temperature_2m_min'][i]
        precipitation = daily['precipitation_probability_max'][i]
        wind_speed = daily['windspeed_10m_max'][i]
        
        # Convert Celsius to Fahrenheit
        temp_max_f = (temp_max * 9/5) + 32
        temp_min_f = (temp_min * 9/5) + 32
        avg_temp = (temp_max_f + temp_min_f) / 2
        
        # Convert km/h to mph
        wind_mph = wind_speed * 0.621371
        
        # Calculate spray score
        score = 100
        reasons = []
        
        # Temperature check (optimal: 50-85°F)
        if avg_temp < 50 or avg_temp > 85:
            score -= 30
            reasons.append(f"Temperature {avg_temp:.0f}°F outside optimal range (50-85°F)")
        elif avg_temp < 55 or avg_temp > 80:
            score -= 15
            reasons.append(f"Temperature {avg_temp:.0f}°F near edge of optimal range")
        
        # Wind check (optimal: < 10 mph)
        if wind_mph > 15:
            score -= 40
            reasons.append(f"Wind speed {wind_mph:.1f} mph too high (max 10 mph)")
        elif wind_mph > 10:
            score -= 20
            reasons.append(f"Wind speed {wind_mph:.1f} mph above optimal (< 10 mph)")
        
        # Precipitation check
        if precipitation > 50:
            score -= 50
            reasons.append(f"High rain probability {precipitation}%")
        elif precipitation > 20:
            score -= 30
            reasons.append(f"Moderate rain probability {precipitation}%")
        elif precipitation > 10:
            score -= 15
            reasons.append(f"Low rain probability {precipitation}%")
        
        score = max(0, score)
        suitable = score >= 70
        
        if suitable and not reasons:
            reasons.append("Good conditions: low wind, no rain, optimal temperature")
        
        spray_windows.append({
            'date': date,
            'suitable': suitable,
            'score': score,
            'reason': '; '.join(reasons) if reasons else 'Excellent spray conditions'
        })
    
    return spray_windows


def get_weather_condition_info(code: int):
    """Map weather code to condition and icon."""
    conditions = {
        0: ('Clear Sky', '☀️'),
        1: ('Mainly Clear', '🌤️'),
        2: ('Partly Cloudy', '⛅'),
        3: ('Overcast', '☁️'),
        45: ('Foggy', '🌫️'),
        48: ('Depositing Rime Fog', '🌫️'),
        51: ('Light Drizzle', '🌦️'),
        53: ('Moderate Drizzle', '🌦️'),
        55: ('Dense Drizzle', '🌧️'),
        61: ('Slight Rain', '🌧️'),
        63: ('Moderate Rain', '🌧️'),
        65: ('Heavy Rain', '⛈️'),
        71: ('Slight Snow', '🌨️'),
        73: ('Moderate Snow', '❄️'),
        75: ('Heavy Snow', '❄️'),
        77: ('Snow Grains', '🌨️'),
        80: ('Slight Rain Showers', '🌦️'),
        81: ('Moderate Rain Showers', '🌧️'),
        82: ('Violent Rain Showers', '⛈️'),
        85: ('Slight Snow Showers', '🌨️'),
        86: ('Heavy Snow Showers', '❄️'),
        95: ('Thunderstorm', '⛈️'),
        96: ('Thunderstorm with Hail', '⛈️'),
        99: ('Thunderstorm with Heavy Hail', '⛈️'),
    }
    return conditions.get(code, ('Unknown', '❓'))


@firestore_fn.on_document_created(document="weatherRequests/{requestId}")
def on_weather_request(event: firestore_fn.Event):
    """Triggered when a new weather request is created."""
    db = firestore.client()
    
    # Get request data
    request_data = event.data.to_dict()
    latitude = request_data.get('latitude')
    longitude = request_data.get('longitude')
    
    if not latitude or not longitude:
        print("Invalid request: missing latitude or longitude")
        return
    
    print(f"Processing weather request for {latitude}, {longitude}")
    
    # Fetch current weather from ETL database
    current_db = get_current_weather_from_db(latitude, longitude)
    
    # Fetch forecast from OpenMeteo
    forecast_data = get_forecast_from_openmeteo(latitude, longitude)
    
    if not forecast_data:
        print("Failed to fetch forecast data")
        return
    
    # Use current weather from API if DB data is stale
    current_weather = forecast_data.get('current_weather', {})
    if current_db:
        # Use DB data if it's more recent (within last hour)
        db_time = current_db.get('timestamp')
        if db_time and (datetime.now() - db_time).total_seconds() < 3600:
            current_weather = {
                'temperature': current_db['temperature'],
                'windspeed': current_db['windSpeed'],
                'winddirection': current_db['windDirection'],
                'weathercode': current_db['weatherCode']
            }
    
    # Build forecast array
    forecast = []
    if 'daily' in forecast_data:
        daily = forecast_data['daily']
        for i in range(len(daily['time'])):
            code = daily['weathercode'][i]
            condition, _ = get_weather_condition_info(code)
            forecast.append({
                'date': daily['time'][i],
                'tempHigh': daily['temperature_2m_max'][i],
                'tempLow': daily['temperature_2m_min'][i],
                'precipitation': daily['precipitation_probability_max'][i],
                'windSpeed': daily['windspeed_10m_max'][i] * 0.621371,  # Convert to mph
                'conditions': condition,
                'weatherCode': code
            })
    
    # Calculate spray windows
    spray_windows = calculate_spray_windows(forecast_data)
    
    # Get weather condition info
    weather_code = current_weather.get('weathercode', 0)
    condition, icon = get_weather_condition_info(weather_code)
    
    # Prepare weather data for Firestore
    weather_data = {
        'location': {
            'latitude': latitude,
            'longitude': longitude
        },
        'current': {
            'temperature': current_weather.get('temperature', 0),
            'humidity': 65,  # OpenMeteo doesn't provide this in free tier
            'windSpeed': current_weather.get('windspeed', 0) * 0.621371,  # Convert to mph
            'windDirection': current_weather.get('winddirection', 0),
            'conditions': condition,
            'weatherCode': weather_code,
            'icon': icon
        },
        'forecast': forecast,
        'sprayWindows': spray_windows,
        'lastUpdated': firestore.SERVER_TIMESTAMP
    }
    
    # Cache in Firestore
    location_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
    db.collection('weather').document(location_key).set(weather_data)
    
    # Update request status
    db.collection('weatherRequests').document(event.params['requestId']).update({
        'status': 'completed',
        'completedAt': firestore.SERVER_TIMESTAMP
    })
    
    print(f"Weather data cached for {latitude}, {longitude}")


@scheduler_fn.on_schedule(schedule="every 1 hours")
def refresh_default_weather(event: scheduler_fn.ScheduledEvent):
    """Refresh weather for default location every hour."""
    db = firestore.client()
    
    # Default location (Kerala, India from your ETL)
    latitude = 10.4597
    longitude = 76.5625
    
    # Create a weather request
    db.collection('weatherRequests').add({
        'latitude': latitude,
        'longitude': longitude,
        'requestedAt': firestore.SERVER_TIMESTAMP,
        'status': 'pending',
        'source': 'scheduled'
    })
    
    print(f"Scheduled weather refresh triggered for {latitude}, {longitude}")

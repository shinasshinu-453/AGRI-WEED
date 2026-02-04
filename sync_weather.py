"""
Standalone Weather Sync Script
Reads from your ETL PostgreSQL database and syncs to Firestore

Run with: python sync_weather.py
"""

import psycopg2
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time
import os

# Initialize Firebase
# Make sure you place your 'serviceAccountKey.json' in this folder!
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    print("✓ Firebase initialized successfully")
except FileNotFoundError:
    print("\n❌ ERROR: 'serviceAccountKey.json' not found!")
    print("Please follow these steps:")
    print("1. Go to Firebase Console -> Project Settings -> Service Accounts")
    print("2. Click 'Generate new private key' and download the JSON file")
    print("3. Rename it to 'serviceAccountKey.json' and place it in this folder:")
    print(f"   {os.getcwd()}")
    exit(1)
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    exit(1)

db = firestore.client()

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

# Default location (from your ETL)
DEFAULT_LOCATION = {
    'latitude': 10.4597,
    'longitude': 76.5625
}

OPENMETEO_API = 'https://api.open-meteo.com/v1/forecast'


def get_weather_from_postgres(latitude, longitude):
    """Fetch latest weather from your PostgreSQL database."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
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
        print(f"❌ PostgreSQL Error: {e}")
        return None


def get_forecast_from_openmeteo(latitude, longitude):
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
        print(f"❌ OpenMeteo Error: {e}")
        return None


def calculate_spray_score(temp_f, wind_mph, precipitation):
    """Calculate spray suitability score (0-100)."""
    score = 100
    
    # Temperature check (optimal: 50-85°F)
    if temp_f < 50 or temp_f > 85:
        score -= 30
    elif temp_f < 55 or temp_f > 80:
        score -= 15
    
    # Wind check (optimal: < 10 mph)
    if wind_mph > 15:
        score -= 40
    elif wind_mph > 10:
        score -= 20
    
    # Precipitation check
    if precipitation > 50:
        score -= 50
    elif precipitation > 20:
        score -= 30
    elif precipitation > 10:
        score -= 15
    
    return max(0, score)


def get_weather_info(code):
    """Map weather code to condition and icon."""
    conditions = {
        0: ('Clear Sky', '☀️'),
        1: ('Mainly Clear', '🌤️'),
        2: ('Partly Cloudy', '⛅'),
        3: ('Overcast', '☁️'),
        61: ('Slight Rain', '🌧️'),
        63: ('Moderate Rain', '🌧️'),
        65: ('Heavy Rain', '⛈️'),
        95: ('Thunderstorm', '⛈️'),
    }
    return conditions.get(code, ('Unknown', '❓'))


def sync_weather(latitude, longitude):
    """Main sync function."""
    print(f"\n🌤️  Syncing weather for {latitude}, {longitude}...")
    
    # 1. Get current weather from PostgreSQL
    print("📊 Fetching from PostgreSQL...")
    pg_weather = get_weather_from_postgres(latitude, longitude)
    
    if pg_weather:
        print(f"   ✓ Temperature: {pg_weather['temperature']}°C")
        print(f"   ✓ Wind: {pg_weather['windSpeed']} km/h")
        print(f"   ✓ Last updated: {pg_weather['timestamp']}")
    else:
        print("   ⚠ No data in PostgreSQL")
    
    # 2. Get forecast from OpenMeteo
    print("🌍 Fetching forecast from OpenMeteo...")
    forecast_data = get_forecast_from_openmeteo(latitude, longitude)
    
    if not forecast_data:
        print("   ❌ Failed to fetch forecast")
        return False
    
    current_weather = forecast_data.get('current_weather', {})
    print(f"   ✓ Current: {current_weather.get('temperature')}°C")
    
    # Use PostgreSQL data if more recent
    if pg_weather:
        pg_time = pg_weather['timestamp']
        if isinstance(pg_time, datetime):
            hours_old = (datetime.now() - pg_time).total_seconds() / 3600
            if hours_old < 1:
                print(f"   ℹ Using PostgreSQL data (fresher)")
                current_weather = {
                    'temperature': pg_weather['temperature'],
                    'windspeed': pg_weather['windSpeed'],
                    'winddirection': pg_weather['windDirection'],
                    'weathercode': pg_weather['weatherCode']
                }
    
    # 3. Build forecast array
    forecast = []
    spray_windows = []
    
    if 'daily' in forecast_data:
        daily = forecast_data['daily']
        for i in range(len(daily['time'])):
            temp_max = daily['temperature_2m_max'][i]
            temp_min = daily['temperature_2m_min'][i]
            precipitation = daily['precipitation_probability_max'][i]
            wind_speed = daily['windspeed_10m_max'][i]
            code = daily['weathercode'][i]
            
            # Convert to imperial
            temp_max_f = (temp_max * 9/5) + 32
            temp_min_f = (temp_min * 9/5) + 32
            avg_temp_f = (temp_max_f + temp_min_f) / 2
            wind_mph = wind_speed * 0.621371
            
            condition, _ = get_weather_info(code)
            
            forecast.append({
                'date': daily['time'][i],
                'tempHigh': temp_max,
                'tempLow': temp_min,
                'precipitation': precipitation,
                'windSpeed': wind_mph,
                'conditions': condition,
                'weatherCode': code
            })
            
            # Calculate spray suitability
            score = calculate_spray_score(avg_temp_f, wind_mph, precipitation)
            suitable = score >= 70
            
            spray_windows.append({
                'date': daily['time'][i],
                'suitable': suitable,
                'score': score,
                'reason': f"Score: {score}/100"
            })
    
    # 4. Prepare data for Firestore
    weather_code = current_weather.get('weathercode', 0)
    condition, icon = get_weather_info(weather_code)
    
    weather_data = {
        'location': {
            'latitude': latitude,
            'longitude': longitude
        },
        'current': {
            'temperature': current_weather.get('temperature', 0),
            'humidity': 65,
            'windSpeed': current_weather.get('windspeed', 0) * 0.621371,
            'windDirection': current_weather.get('winddirection', 0),
            'conditions': condition,
            'weatherCode': weather_code,
            'icon': icon
        },
        'forecast': forecast,
        'sprayWindows': spray_windows,
        'lastUpdated': firestore.SERVER_TIMESTAMP
    }
    
    # 5. Save to Firestore
    try:
        location_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
        db.collection('weather').document(location_key).set(weather_data)
        print(f"✅ Synced to Firestore: /weather/{location_key}")
        
        # Print spray recommendations
        suitable_days = [w for w in spray_windows if w['suitable']]
        print(f"\n🌾 Spray Windows: {len(suitable_days)}/7 days suitable")
        for w in suitable_days[:3]:
            print(f"   ✓ {w['date']}: Score {w['score']}/100")
        
        return True
    except Exception as e:
        print(f"❌ Firestore Error: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🌤️  Weather Sync Script")
    print("=" * 60)
    
    # Test PostgreSQL connection
    print("\n🔍 Testing PostgreSQL connection...")
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        count = cursor.fetchone()[0]
        print(f"   ✓ Connected! Found {count} weather records")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n💡 Make sure your ETL pipeline is running:")
        print("   cd 'C:\\Users\\shina\\ETL PIPELINE'")
        print("   docker-compose up")
        exit(1)
    
    # Sync weather
    success = sync_weather(
        DEFAULT_LOCATION['latitude'],
        DEFAULT_LOCATION['longitude']
    )
    
    if success:
        print("\n✅ Weather sync complete!")
        print("\n💡 To run automatically, add to cron/scheduler:")
        print("   Every hour: python sync_weather.py")
    else:
        print("\n❌ Weather sync failed!")
    
    print("=" * 60)

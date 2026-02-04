# Test script to debug weather sync issue
import psycopg2
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
try:
    firebase_admin.initialize_app(cred)
except ValueError:
    pass  # Already initialized
db = firestore.client()

# Test PostgreSQL
print('Testing PostgreSQL...')
try:
    conn = psycopg2.connect(
        host='localhost', 
        database='postgres', 
        user='postgres', 
        password='postgres', 
        port='5432'
    )
    cursor = conn.cursor()
    cursor.execute('''
        SELECT temperature, windspeed, winddirection, weathercode, timestamp 
        FROM weather_data 
        WHERE latitude = 10.4597 AND longitude = 76.5625 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''')
    result = cursor.fetchone()
    if result:
        print(f'PostgreSQL data:')
        print(f'  Temperature: {result[0]} C')
        print(f'  Windspeed: {result[1]} km/h')
        print(f'  Timestamp: {result[4]}')
    else:
        print('No data found for default location!')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'PostgreSQL Error: {e}')

# Test OpenMeteo
print('\nTesting OpenMeteo...')
try:
    response = requests.get('https://api.open-meteo.com/v1/forecast', params={
        'latitude': 10.4597, 
        'longitude': 76.5625, 
        'current_weather': True
    })
    if response.status_code == 200:
        data = response.json()
        temp = data.get('current_weather', {}).get('temperature')
        print(f'OpenMeteo OK - Current temp: {temp} C')
    else:
        print(f'OpenMeteo Error: {response.status_code}')
except Exception as e:
    print(f'OpenMeteo Error: {e}')

# Check Firestore
print('\nChecking Firestore...')
from datetime import datetime as dt
try:
    doc = db.collection('weather').document('10.46_76.56').get()
    if doc.exists:
        data = doc.to_dict()
        current = data.get('current', {})
        last_updated = data.get('lastUpdated')
        print('Firestore data EXISTS:')
        print('  Temperature:', current.get('temperature'), 'C')
        print('  Conditions:', current.get('conditions'))
        print('  Icon:', current.get('icon'))
        if last_updated:
            ts = last_updated.seconds
            updated_dt = dt.fromtimestamp(ts)
            print('  Last Updated:', updated_dt)
            hours_old = (dt.now() - updated_dt).total_seconds() / 3600
            print('  Hours old:', round(hours_old, 2))
            if hours_old > 1:
                print('  WARNING: Data is stale (> 1 hour old)!')
        
        # Also check forecast
        forecast = data.get('forecast', [])
        print('  Forecast days:', len(forecast))
    else:
        print('NO Firestore data found - Need to run sync_weather.py!')
except Exception as e:
    print('Firestore Error:', e)

print('\n--- Done ---')

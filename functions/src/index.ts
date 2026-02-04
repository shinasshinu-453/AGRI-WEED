import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import {
    getCurrentWeatherFromETL,
    getForecastFromOpenMeteo,
    getWeatherConditionInfo,
    calculateSprayWindows,
    FullWeatherResponse
} from './weatherService';

admin.initializeApp();

/**
 * Triggered when a new weather request is created.
 */
export const onWeatherRequest = functions.firestore
    .document('weatherRequests/{requestId}')
    .onCreate(async (snapshot, context) => {
        const data = snapshot.data();
        if (!data) return null;

        const lat = data.latitude;
        const lon = data.longitude;

        if (!lat || !lon) {
            console.error('Missing latitude/longitude in request');
            return null;
        }

        console.log(`Processing weather request for ${lat}, ${lon}`);

        try {
            // 1. Refresh from ETL if available
            const currentETL = await getCurrentWeatherFromETL(lat, lon);

            // 2. Refresh from OpenMeteo
            const forecastData = await getForecastFromOpenMeteo(lat, lon);
            if (!forecastData) {
                throw new Error('Failed to fetch forecast from OpenMeteo');
            }

            // 3. Determine current weather (prefer ETL if fresh, fallback to OpenMeteo)
            let current = forecastData.current_weather;
            if (currentETL) {
                const etlTime = new Date(currentETL.timestamp).getTime();
                const now = Date.now();
                // Use ETL if it's less than 2 hours old
                if (now - etlTime < 2 * 60 * 60 * 1000) {
                    current = {
                        temperature: currentETL.temperature,
                        windspeed: currentETL.windSpeed,
                        winddirection: currentETL.windDirection,
                        weathercode: currentETL.weatherCode
                    };
                }
            }

            const [condition, icon] = getWeatherConditionInfo(current.weathercode);

            // 4. Build Forecast
            const forecast = [];
            if (forecastData.daily) {
                const daily = forecastData.daily;
                for (let i = 0; i < daily.time.length; i++) {
                    const code = daily.weathercode[i];
                    const [dayCondition] = getWeatherConditionInfo(code);
                    forecast.push({
                        date: daily.time[i],
                        tempHigh: daily.temperature_2m_max[i],
                        tempLow: daily.temperature_2m_min[i],
                        precipitation: daily.precipitation_probability_max[i],
                        windSpeed: daily.windspeed_10m_max[i] * 0.621371, // mph
                        conditions: dayCondition,
                        weatherCode: code
                    });
                }
            }

            // 5. Calculate Spray Windows
            const sprayWindows = calculateSprayWindows(forecastData);

            // 6. Compile Final Data
            const weatherData: FullWeatherResponse = {
                location: { latitude: lat, longitude: lon },
                current: {
                    temperature: current.temperature,
                    humidity: 65, // Static fallback
                    windSpeed: current.windspeed * 0.621371, // mph
                    windDirection: current.winddirection,
                    conditions: condition,
                    weatherCode: current.weathercode,
                    icon: icon
                },
                forecast,
                sprayWindows,
                lastUpdated: admin.firestore.FieldValue.serverTimestamp()
            };

            // 7. Save to Cache
            const locationKey = `${Math.round(lat * 100) / 100}_${Math.round(lon * 100) / 100}`;
            await admin.firestore().collection('weather').document(locationKey).set(weatherData);

            // 8. Update request status
            await snapshot.ref.update({
                status: 'completed',
                completedAt: admin.firestore.FieldValue.serverTimestamp()
            });

            console.log(`Weather updated successfully for key: ${locationKey}`);
            return null;
        } catch (error) {
            console.error('Error processing weather request:', error);
            await snapshot.ref.update({
                status: 'failed',
                error: error instanceof Error ? error.message : String(error)
            });
            return null;
        }
    });

/**
 * Scheduled refresh every hour for the default location.
 */
export const refreshDefaultWeather = functions.pubsub
    .schedule('every 1 hours')
    .onRun(async (context) => {
        const lat = 10.4597; // Default Kerala location
        const lon = 76.5625;

        console.log(`Scheduled refresh triggered for ${lat}, ${lon}`);

        await admin.firestore().collection('weatherRequests').add({
            latitude: lat,
            longitude: lon,
            requestedAt: admin.firestore.FieldValue.serverTimestamp(),
            status: 'pending',
            source: 'scheduled'
        });

        return null;
    });

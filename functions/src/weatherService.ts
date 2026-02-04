import axios from 'axios';
import { Timestamp } from 'firebase-admin/firestore';

// Types
export interface WeatherData {
    latitude: number;
    longitude: number;
    temperature: number;
    windSpeed: number;
    windDirection: number;
    weatherCode: number;
    timestamp: string;
}

export interface ForecastDay {
    date: string;
    tempHigh: number;
    tempLow: number;
    precipitation: number;
    windSpeed: number;
    conditions: string;
    weatherCode: number;
}

export interface SprayWindow {
    date: string;
    suitable: boolean;
    score: number;
    reason: string;
}

export interface FullWeatherResponse {
    location: {
        latitude: number;
        longitude: number;
    };
    current: {
        temperature: number;
        humidity: number;
        windSpeed: number;
        windDirection: number;
        conditions: string;
        weatherCode: number;
        icon: string;
    };
    forecast: ForecastDay[];
    sprayWindows: SprayWindow[];
    lastUpdated: any;
}

// Constants
const OPENMETEO_API = 'https://api.open-meteo.com/v1/forecast';
const WEATHER_API_URL = process.env.WEATHER_API_URL || 'http://localhost:5000';

/**
 * Fetch latest weather data from the ETL pipeline's REST API.
 */
export async function getCurrentWeatherFromETL(lat: number, lon: number): Promise<WeatherData | null> {
    try {
        // Note: The /api/weather/latest endpoint current returns the very latest data regardless of lat/lon
        // In a production app, you might want to filter by coordinates.
        const response = await axios.get(`${WEATHER_API_URL}/api/weather/latest`, {
            timeout: 5000
        });

        if (response.status === 200) {
            return {
                latitude: response.data.latitude,
                longitude: response.data.longitude,
                temperature: response.data.temperature,
                windSpeed: response.data.windspeed,
                windDirection: response.data.winddirection,
                weatherCode: response.data.weathercode,
                timestamp: response.data.timestamp
            };
        }
        return null;
    } catch (error) {
        console.error(`Error fetching from ETL API: ${error}`);
        return null;
    }
}

/**
 * Fetch 7-day forecast from OpenMeteo API.
 */
export async function getForecastFromOpenMeteo(lat: number, lon: number) {
    try {
        const params = {
            latitude: lat,
            longitude: lon,
            current_weather: true,
            daily: 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max,weathercode',
            timezone: 'auto',
            forecast_days: 7
        };

        const response = await axios.get(OPENMETEO_API, { params, timeout: 10000 });
        return response.data;
    } catch (error) {
        console.error(`Error fetching from OpenMeteo: ${error}`);
        return null;
    }
}

/**
 * Map weather code to condition and icon.
 */
export function getWeatherConditionInfo(code: number): [string, string] {
    const conditions: Record<number, [string, string]> = {
        0: ['Clear Sky', '☀️'],
        1: ['Mainly Clear', '🌤️'],
        2: ['Partly Cloudy', '⛅'],
        3: ['Overcast', '☁️'],
        45: ['Foggy', '🌫️'],
        48: ['Depositing Rime Fog', '🌫️'],
        51: ['Light Drizzle', '🌦️'],
        53: ['Moderate Drizzle', '🌦️'],
        55: ['Dense Drizzle', '🌧️'],
        61: ['Slight Rain', '🌧️'],
        63: ['Moderate Rain', '🌧️'],
        65: ['Heavy Rain', '⛈️'],
        71: ['Slight Snow', '🌨️'],
        73: ['Moderate Snow', '❄️'],
        75: ['Heavy Snow', '❄️'],
        77: ['Snow Grains', '🌨️'],
        80: ['Slight Rain Showers', '🌦️'],
        81: ['Moderate Rain Showers', '🌧️'],
        82: ['Violent Rain Showers', '⛈️'],
        85: ['Slight Snow Showers', '🌨️'],
        86: ['Heavy Snow Showers', '❄️'],
        95: ['Thunderstorm', '⛈️'],
        96: ['Thunderstorm with Hail', '⛈️'],
        99: ['Thunderstorm with Heavy Hail', '⛈️'],
    };
    return conditions[code] || ['Unknown', '❓'];
}

/**
 * Calculate spray suitability windows.
 */
export function calculateSprayWindows(forecastData: any): SprayWindow[] {
    const sprayWindows: SprayWindow[] = [];

    if (!forecastData || !forecastData.daily) {
        return sprayWindows;
    }

    const daily = forecastData.daily;

    for (let i = 0; i < daily.time.length; i++) {
        const date = daily.time[i];
        const tempMax = daily.temperature_2m_max[i];
        const tempMin = daily.temperature_2m_min[i];
        const precipitation = daily.precipitation_probability_max[i];
        const windSpeed = daily.windspeed_10m_max[i];

        // Convert to imperial for calculation
        const avgTempF = ((tempMax + tempMin) / 2) * 1.8 + 32;
        const windMph = windSpeed * 0.621371;

        let score = 100;
        const reasons: string[] = [];

        // Temperature check (optimal: 50-85°F)
        if (avgTempF < 50 || avgTempF > 85) {
            score -= 30;
            reasons.push(`Temperature ${avgTempF.toFixed(0)}°F outside optimal range (50-85°F)`);
        } else if (avgTempF < 55 || avgTempF > 80) {
            score -= 15;
            reasons.push(`Temperature ${avgTempF.toFixed(0)}°F near edge of optimal range`);
        }

        // Wind check (optimal: < 10 mph)
        if (windMph > 15) {
            score -= 40;
            reasons.push(`Wind speed ${windMph.toFixed(1)} mph too high (max 10 mph)`);
        } else if (windMph > 10) {
            score -= 20;
            reasons.push(`Wind speed ${windMph.toFixed(1)} mph above optimal (< 10 mph)`);
        }

        // Precipitation check
        if (precipitation > 50) {
            score -= 50;
            reasons.push(`High rain probability ${precipitation}%`);
        } else if (precipitation > 20) {
            score -= 30;
            reasons.push(`Moderate rain probability ${precipitation}%`);
        } else if (precipitation > 10) {
            score -= 15;
            reasons.push(`Low rain probability ${precipitation}%`);
        }

        score = Math.max(0, score);
        const suitable = score >= 70;

        if (suitable && reasons.length === 0) {
            reasons.push("Good conditions: low wind, no rain, optimal temperature");
        }

        sprayWindows.push({
            date,
            suitable,
            score,
            reason: reasons.length > 0 ? reasons.join('; ') : 'Excellent spray conditions'
        });
    }

    return sprayWindows;
}

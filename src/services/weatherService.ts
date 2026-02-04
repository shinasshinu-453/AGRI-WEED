// Weather Service - Fetches weather data from Firebase/Firestore cache
import { collection, doc, getDoc, setDoc, Timestamp, query, where, getDocs } from 'firebase/firestore';
import { db } from '../lib/firebase';

export interface WeatherCurrent {
    temperature: number;
    humidity: number;
    windSpeed: number;
    windDirection: number;
    conditions: string;
    weatherCode: number;
    icon: string;
}

export interface WeatherForecast {
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
    reason: string;
    score: number; // 0-100
}

export interface WeatherData {
    location: {
        latitude: number;
        longitude: number;
        name?: string;
    };
    current: WeatherCurrent;
    forecast: WeatherForecast[];
    sprayWindows: SprayWindow[];
    lastUpdated: Timestamp;
}

// Weather code to condition mapping (OpenMeteo codes)
const WEATHER_CONDITIONS: Record<number, { condition: string; icon: string }> = {
    0: { condition: 'Clear Sky', icon: '☀️' },
    1: { condition: 'Mainly Clear', icon: '🌤️' },
    2: { condition: 'Partly Cloudy', icon: '⛅' },
    3: { condition: 'Overcast', icon: '☁️' },
    45: { condition: 'Foggy', icon: '🌫️' },
    48: { condition: 'Depositing Rime Fog', icon: '🌫️' },
    51: { condition: 'Light Drizzle', icon: '🌦️' },
    53: { condition: 'Moderate Drizzle', icon: '🌦️' },
    55: { condition: 'Dense Drizzle', icon: '🌧️' },
    61: { condition: 'Slight Rain', icon: '🌧️' },
    63: { condition: 'Moderate Rain', icon: '🌧️' },
    65: { condition: 'Heavy Rain', icon: '⛈️' },
    71: { condition: 'Slight Snow', icon: '🌨️' },
    73: { condition: 'Moderate Snow', icon: '❄️' },
    75: { condition: 'Heavy Snow', icon: '❄️' },
    77: { condition: 'Snow Grains', icon: '🌨️' },
    80: { condition: 'Slight Rain Showers', icon: '🌦️' },
    81: { condition: 'Moderate Rain Showers', icon: '🌧️' },
    82: { condition: 'Violent Rain Showers', icon: '⛈️' },
    85: { condition: 'Slight Snow Showers', icon: '🌨️' },
    86: { condition: 'Heavy Snow Showers', icon: '❄️' },
    95: { condition: 'Thunderstorm', icon: '⛈️' },
    96: { condition: 'Thunderstorm with Hail', icon: '⛈️' },
    99: { condition: 'Thunderstorm with Heavy Hail', icon: '⛈️' },
};

const getWeatherInfo = (code: number) => {
    return WEATHER_CONDITIONS[code] || { condition: 'Unknown', icon: '❓' };
};

// Calculate spray suitability score
const calculateSprayScore = (temp: number, windSpeed: number, precipitation: number): number => {
    let score = 100;

    // Temperature penalty (optimal: 50-85°F)
    if (temp < 50 || temp > 85) score -= 30;
    else if (temp < 55 || temp > 80) score -= 15;

    // Wind penalty (optimal: < 10 mph)
    if (windSpeed > 15) score -= 40;
    else if (windSpeed > 10) score -= 20;
    else if (windSpeed > 5) score -= 10;

    // Precipitation penalty
    if (precipitation > 50) score -= 50;
    else if (precipitation > 20) score -= 30;
    else if (precipitation > 10) score -= 15;

    return Math.max(0, score);
};

// Get weather data from Firestore cache
export const getWeatherData = async (latitude: number, longitude: number): Promise<WeatherData | null> => {
    try {
        // Round coordinates to 2 decimal places for caching
        const lat = Math.round(latitude * 100) / 100;
        const lon = Math.round(longitude * 100) / 100;
        const locationKey = `${lat}_${lon}`;

        const weatherDoc = await getDoc(doc(db, 'weather', locationKey));

        if (weatherDoc.exists()) {
            const data = weatherDoc.data();

            // Check if data is fresh (less than 1 hour old)
            const lastUpdated = data.lastUpdated.toDate();
            const now = new Date();
            const hoursSinceUpdate = (now.getTime() - lastUpdated.getTime()) / (1000 * 60 * 60);

            if (hoursSinceUpdate < 1) {
                return data as WeatherData;
            }
        }

        // If no cached data or stale, trigger Cloud Function to fetch new data
        await triggerWeatherUpdate(lat, lon);

        // Return null to indicate data is being fetched
        return null;
    } catch (error) {
        console.error('Error fetching weather data:', error);
        throw error;
    }
};

// Trigger Cloud Function to update weather data
const triggerWeatherUpdate = async (latitude: number, longitude: number): Promise<void> => {
    try {
        // This will be called by the Cloud Function
        // For now, we'll create a request document that the function watches
        await setDoc(doc(db, 'weatherRequests', `${latitude}_${longitude}`), {
            latitude,
            longitude,
            requestedAt: Timestamp.now(),
            status: 'pending'
        });
    } catch (error) {
        console.error('Error triggering weather update:', error);
    }
};

// Subscribe to weather updates
export const subscribeToWeather = (
    latitude: number,
    longitude: number,
    callback: (weather: WeatherData | null) => void
): (() => void) => {
    const lat = Math.round(latitude * 100) / 100;
    const lon = Math.round(longitude * 100) / 100;
    const locationKey = `${lat}_${lon}`;

    // Set up real-time listener
    const unsubscribe = () => {
        // Firestore onSnapshot would go here
        // For now, poll every 5 minutes
        const interval = setInterval(async () => {
            const weather = await getWeatherData(latitude, longitude);
            callback(weather);
        }, 5 * 60 * 1000);

        return () => clearInterval(interval);
    };

    // Initial fetch
    getWeatherData(latitude, longitude).then(callback);

    return unsubscribe();
};

// Get default location (from user profile or use default)
export const getDefaultLocation = (): { latitude: number; longitude: number } => {
    // Default to Kerala, India (from your ETL pipeline)
    return {
        latitude: 10.4597,
        longitude: 76.5625
    };
};

// Format temperature based on user preference
export const formatTemperature = (celsius: number, unit: 'C' | 'F' = 'C'): string => {
    if (unit === 'F') {
        const fahrenheit = (celsius * 9 / 5) + 32;
        return `${Math.round(fahrenheit)}°F`;
    }
    return `${Math.round(celsius)}°C`;
};

// Get spray recommendation based on weather
export const getSprayRecommendation = (weather: WeatherData): {
    canSpray: boolean;
    message: string;
    bestDays: string[];
} => {
    const suitableWindows = weather.sprayWindows.filter(w => w.suitable && w.score >= 70);

    if (suitableWindows.length === 0) {
        return {
            canSpray: false,
            message: 'No suitable spray windows in the next 7 days. Wait for better conditions.',
            bestDays: []
        };
    }

    const bestDays = suitableWindows
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
        .map(w => w.date);

    return {
        canSpray: true,
        message: `${suitableWindows.length} suitable spray window(s) available.`,
        bestDays
    };
};

// Weather Service - Fetches directly from Open Meteo API (no Firebase required)

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
    lastUpdated: { toDate: () => Date };
}

// Weather code to condition + icon mapping (WMO / OpenMeteo codes)
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
    99: { condition: 'Thunderstorm + Heavy Hail', icon: '⛈️' },
};

const getWeatherInfo = (code: number) =>
    WEATHER_CONDITIONS[code] || { condition: 'Unknown', icon: '🌡️' };

// Spray suitability score (0-100)
const calculateSprayScore = (tempC: number, windKmh: number, precipPct: number): number => {
    let score = 100;
    const tempF = (tempC * 9 / 5) + 32;

    if (tempF < 50 || tempF > 85) score -= 30;
    else if (tempF < 55 || tempF > 80) score -= 15;

    const windMph = windKmh * 0.621371;
    if (windMph > 15) score -= 40;
    else if (windMph > 10) score -= 20;
    else if (windMph > 5) score -= 10;

    if (precipPct > 50) score -= 50;
    else if (precipPct > 20) score -= 30;
    else if (precipPct > 10) score -= 15;

    return Math.max(0, score);
};

// In-memory cache (valid for 30 minutes)
const _cache: Record<string, { data: WeatherData; fetchedAt: number }> = {};

/**
 * Fetch weather directly from Open Meteo — no Firebase, no Cloud Functions.
 */
export const getWeatherData = async (
    latitude: number,
    longitude: number,
    locationName?: string,
    _userId?: string   // kept for API compatibility, not used
): Promise<WeatherData | null> => {
    const lat = Math.round(latitude * 100) / 100;
    const lon = Math.round(longitude * 100) / 100;
    const cacheKey = `${lat}_${lon}`;

    // Return cached data if fresh (< 30 min)
    const cached = _cache[cacheKey];
    if (cached && Date.now() - cached.fetchedAt < 30 * 60 * 1000) {
        return cached.data;
    }

    const url =
        `https://api.open-meteo.com/v1/forecast` +
        `?latitude=${lat}&longitude=${lon}` +
        `&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code` +
        `&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,weather_code` +
        `&timezone=auto` +
        `&forecast_days=7`;

    const response = await fetch(url);
    if (!response.ok) throw new Error(`Open Meteo error: ${response.status}`);

    const raw = await response.json();

    // --- Current weather ---
    const cur = raw.current;
    const curInfo = getWeatherInfo(cur.weather_code);
    const currentWeather: WeatherCurrent = {
        temperature: cur.temperature_2m,
        humidity: cur.relative_humidity_2m,
        windSpeed: cur.wind_speed_10m * 0.621371,  // km/h → mph
        windDirection: cur.wind_direction_10m,
        conditions: curInfo.condition,
        weatherCode: cur.weather_code,
        icon: curInfo.icon,
    };

    // --- 7-day forecast + spray windows ---
    const daily = raw.daily;
    const forecast: WeatherForecast[] = [];
    const sprayWindows: SprayWindow[] = [];

    for (let i = 0; i < daily.time.length; i++) {
        const code = daily.weather_code[i];
        const info = getWeatherInfo(code);
        const wind = daily.wind_speed_10m_max[i];   // km/h
        const precip = daily.precipitation_probability_max[i] ?? 0;
        const tHigh = daily.temperature_2m_max[i];
        const tLow = daily.temperature_2m_min[i];

        forecast.push({
            date: daily.time[i],
            tempHigh: tHigh,
            tempLow: tLow,
            precipitation: precip,
            windSpeed: wind * 0.621371,  // km/h → mph
            conditions: info.condition,
            weatherCode: code,
        });

        const score = calculateSprayScore(tHigh, wind, precip);
        let reason = '';
        if (score >= 70) reason = 'Good temperature, low wind, minimal rain chance.';
        else if (precip > 50) reason = 'High precipitation risk — avoid spraying.';
        else if (wind > 24) reason = 'Wind too strong for accurate spraying.';
        else reason = 'Marginal conditions — spray with caution.';

        sprayWindows.push({
            date: daily.time[i],
            suitable: score >= 70,
            reason,
            score,
        });
    }

    const now = new Date();
    const weatherData: WeatherData = {
        location: { latitude: lat, longitude: lon, name: locationName },
        current: currentWeather,
        forecast,
        sprayWindows,
        // Match the Timestamp-like interface so existing UI code works
        lastUpdated: { toDate: () => now },
    };

    _cache[cacheKey] = { data: weatherData, fetchedAt: Date.now() };
    return weatherData;
};

/** Default location — Kerala, India */
export const getDefaultLocation = (): { latitude: number; longitude: number } => ({
    latitude: 10.4597,
    longitude: 76.5625,
});

/** Format temperature in °C or °F */
export const formatTemperature = (celsius: number, unit: 'C' | 'F' = 'C'): string => {
    if (unit === 'F') return `${Math.round((celsius * 9 / 5) + 32)}°F`;
    return `${Math.round(celsius)}°C`;
};

/** Get human-friendly spray recommendation */
export const getSprayRecommendation = (weather: WeatherData): {
    canSpray: boolean;
    message: string;
    bestDays: string[];
} => {
    const suitable = weather.sprayWindows.filter(w => w.suitable && w.score >= 70);
    if (suitable.length === 0) {
        return {
            canSpray: false,
            message: 'No suitable spray windows in the next 7 days. Wait for better conditions.',
            bestDays: [],
        };
    }
    const bestDays = suitable
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
        .map(w => w.date);
    return {
        canSpray: true,
        message: `${suitable.length} suitable spray window(s) available.`,
        bestDays,
    };
};

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
    Cloud,
    Droplets,
    Wind,
    AlertTriangle,
    CheckCircle,
    XCircle,
    RefreshCw,
    MapPin
} from 'lucide-react';
import {
    getWeatherData,
    getDefaultLocation,
    formatTemperature,
    getSprayRecommendation,
    WeatherData
} from '../services/weatherService';
import { Button } from './ui/button';

export const WeatherWidget: React.FC<{
    latitude?: number;
    longitude?: number;
    compact?: boolean;
}> = ({ latitude, longitude, compact = false }) => {
    const [weather, setWeather] = useState<WeatherData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const location = latitude && longitude
        ? { latitude, longitude }
        : getDefaultLocation();

    const fetchWeather = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getWeatherData(location.latitude, location.longitude);
            if (data) {
                setWeather(data);
            } else {
                setError('Fetching weather data... Please wait.');
            }
        } catch (err: any) {
            setError(err.message || 'Failed to fetch weather data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWeather();
        // Refresh every 30 minutes
        const interval = setInterval(fetchWeather, 30 * 60 * 1000);
        return () => clearInterval(interval);
    }, [location.latitude, location.longitude]);

    if (loading && !weather) {
        return (
            <Card className="glass-effect border-white/20">
                <CardContent className="p-6">
                    <div className="flex items-center justify-center gap-2 text-muted-foreground">
                        <RefreshCw className="animate-spin" size={20} />
                        <span>Loading weather data...</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error && !weather) {
        return (
            <Card className="glass-effect border-white/20">
                <CardContent className="p-6">
                    <div className="flex items-center gap-2 text-yellow-600">
                        <AlertTriangle size={20} />
                        <span className="text-sm">{error}</span>
                    </div>
                    <Button
                        onClick={fetchWeather}
                        variant="outline"
                        size="sm"
                        className="mt-4"
                    >
                        <RefreshCw size={16} className="mr-2" />
                        Retry
                    </Button>
                </CardContent>
            </Card>
        );
    }

    if (!weather) return null;

    const sprayRec = getSprayRecommendation(weather);

    if (compact) {
        return (
            <Card className="glass-effect border-white/20">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">{weather.current.icon}</span>
                            <div>
                                <p className="text-2xl font-bold">
                                    {formatTemperature(weather.current.temperature)}
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    {weather.current.conditions}
                                </p>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="flex items-center gap-2 text-sm">
                                <Wind size={16} />
                                <span>{Math.round(weather.current.windSpeed)} mph</span>
                            </div>
                            {sprayRec.canSpray ? (
                                <Badge className="mt-2 bg-green-500">
                                    <CheckCircle size={12} className="mr-1" />
                                    Can Spray
                                </Badge>
                            ) : (
                                <Badge variant="destructive" className="mt-2">
                                    <XCircle size={12} className="mr-1" />
                                    Wait
                                </Badge>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="glass-effect border-white/20">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <Cloud size={20} />
                        Weather Forecast
                    </CardTitle>
                    <Button
                        onClick={fetchWeather}
                        variant="ghost"
                        size="sm"
                        disabled={loading}
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    </Button>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin size={14} />
                    <span>
                        {location.latitude.toFixed(2)}°N, {location.longitude.toFixed(2)}°E
                    </span>
                </div>
            </CardHeader>

            <CardContent className="space-y-6">
                {/* Current Weather */}
                <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-white/10">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <p className="text-sm text-muted-foreground mb-1">Current Conditions</p>
                            <p className="text-4xl font-bold">
                                {formatTemperature(weather.current.temperature)}
                            </p>
                            <p className="text-lg text-muted-foreground mt-1">
                                {weather.current.conditions}
                            </p>
                        </div>
                        <span className="text-6xl">{weather.current.icon}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                        <div className="flex items-center gap-2">
                            <Wind size={18} className="text-blue-400" />
                            <div>
                                <p className="text-xs text-muted-foreground">Wind Speed</p>
                                <p className="font-semibold">{Math.round(weather.current.windSpeed)} mph</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <Droplets size={18} className="text-blue-400" />
                            <div>
                                <p className="text-xs text-muted-foreground">Humidity</p>
                                <p className="font-semibold">{weather.current.humidity}%</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Spray Recommendation */}
                <div className={`rounded-xl p-4 border ${sprayRec.canSpray
                        ? 'bg-green-500/10 border-green-500/30'
                        : 'bg-red-500/10 border-red-500/30'
                    }`}>
                    <div className="flex items-start gap-3">
                        {sprayRec.canSpray ? (
                            <CheckCircle size={24} className="text-green-500 flex-shrink-0 mt-0.5" />
                        ) : (
                            <XCircle size={24} className="text-red-500 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                            <h4 className="font-semibold mb-1">
                                {sprayRec.canSpray ? 'Good Spray Conditions' : 'Poor Spray Conditions'}
                            </h4>
                            <p className="text-sm text-muted-foreground mb-2">
                                {sprayRec.message}
                            </p>
                            {sprayRec.bestDays.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {sprayRec.bestDays.map(day => (
                                        <Badge key={day} variant="outline" className="bg-white/5">
                                            {new Date(day).toLocaleDateString('en-US', {
                                                weekday: 'short',
                                                month: 'short',
                                                day: 'numeric'
                                            })}
                                        </Badge>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* 7-Day Forecast */}
                <div>
                    <h4 className="font-semibold mb-3">7-Day Forecast</h4>
                    <div className="space-y-2">
                        {weather.forecast.slice(0, 7).map((day, index) => {
                            const sprayWindow = weather.sprayWindows.find(w => w.date === day.date);
                            return (
                                <div
                                    key={day.date}
                                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                    <div className="flex items-center gap-3 flex-1">
                                        <span className="text-2xl">
                                            {day.weatherCode !== undefined
                                                ? String.fromCodePoint(0x2600 + (day.weatherCode % 10))
                                                : '☀️'}
                                        </span>
                                        <div className="flex-1">
                                            <p className="font-medium">
                                                {index === 0 ? 'Today' : new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                                            </p>
                                            <p className="text-xs text-muted-foreground">{day.conditions}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="text-right">
                                            <p className="font-semibold">
                                                {formatTemperature(day.tempHigh)} / {formatTemperature(day.tempLow)}
                                            </p>
                                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                <Droplets size={12} />
                                                <span>{day.precipitation}%</span>
                                            </div>
                                        </div>
                                        {sprayWindow && (
                                            <div className="w-16">
                                                {sprayWindow.suitable ? (
                                                    <Badge className="bg-green-500 text-xs">
                                                        ✓ Spray
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="secondary" className="text-xs">
                                                        ✗ Wait
                                                    </Badge>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Last Updated */}
                <p className="text-xs text-muted-foreground text-center">
                    Last updated: {weather.lastUpdated.toDate().toLocaleString()}
                </p>
            </CardContent>
        </Card>
    );
};

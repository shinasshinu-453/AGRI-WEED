// Location service for geolocation tracking
export interface LocationData {
    latitude: number;
    longitude: number;
    accuracy: number;
    timestamp: number;
    locationName?: string;
}

export const getCurrentLocation = (): Promise<LocationData> => {
    return new Promise((resolve, reject) => {
        // Geolocation only works on secure origins (HTTPS or localhost)
        if (!window.isSecureContext) {
            reject(new Error('Location requires HTTPS. Access the app via https://'));
            return;
        }

        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const locationData: LocationData = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: position.timestamp,
                };

                // Try to get location name via reverse geocoding
                try {
                    const name = await getLocationName(
                        locationData.latitude,
                        locationData.longitude
                    );
                    locationData.locationName = name;
                } catch (err) {
                    console.warn('Failed to get location name:', err);
                }

                resolve(locationData);
            },
            (error) => {
                let message = 'Failed to get location';
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        message = 'Location permission denied';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = 'Location information unavailable';
                        break;
                    case error.TIMEOUT:
                        message = 'Location request timed out';
                        break;
                }
                reject(new Error(message));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000, // Cache for 5 minutes
            }
        );
    });
};

export const getLocationName = async (
    latitude: number,
    longitude: number
): Promise<string> => {
    try {
        // Using OpenStreetMap Nominatim API (free, no API key needed)
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10`
        );

        if (!response.ok) {
            throw new Error('Geocoding request failed');
        }

        const data = await response.json();

        // Build a readable location string
        const parts = [];
        if (data.address.city) parts.push(data.address.city);
        else if (data.address.town) parts.push(data.address.town);
        else if (data.address.village) parts.push(data.address.village);

        if (data.address.state) parts.push(data.address.state);
        if (data.address.country) parts.push(data.address.country);

        return parts.join(', ') || 'Unknown Location';
    } catch (error) {
        console.error('Reverse geocoding failed:', error);
        return `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
    }
};

export const checkLocationPermission = async (): Promise<'granted' | 'denied' | 'prompt'> => {
    if (!navigator.permissions) {
        return 'prompt';
    }

    try {
        const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName });
        return result.state as 'granted' | 'denied' | 'prompt';
    } catch (error) {
        return 'prompt';
    }
};

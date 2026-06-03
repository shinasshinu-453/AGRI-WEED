import { useEffect, useState } from 'react';

export function DebugAPIURL() {
    const [apiUrl, setApiUrl] = useState<string>('');

    useEffect(() => {
        setApiUrl(import.meta.env.VITE_API_URL || 'NOT SET');
        console.log('🔍 VITE_API_URL:', import.meta.env.VITE_API_URL);
        console.log('🔍 All env vars:', import.meta.env);
    }, []);

    return (
        <div style={{
            position: 'fixed',
            bottom: 10,
            right: 10,
            background: 'red',
            color: 'white',
            padding: '10px',
            zIndex: 9999,
            fontSize: '12px',
            fontFamily: 'monospace'
        }}>
            <div>VITE_API_URL: {apiUrl}</div>
        </div>
    );
}

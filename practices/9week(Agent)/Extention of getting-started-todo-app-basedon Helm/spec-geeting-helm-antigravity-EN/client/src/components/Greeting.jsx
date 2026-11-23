import { useState, useEffect } from 'react';
import { Alert } from 'react-bootstrap';

export default function Greeting() {
    const [greeting, setGreeting] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        let isMounted = true;
        fetch('/api/greeting')
            .then(async (response) => {
                if (!response.ok) {
                    throw new Error('Failed to load greeting');
                }
                return response.json();
            })
            .then((data) => {
                if (isMounted && data.greeting) {
                    setGreeting(data.greeting);
                }
            })
            .catch((err) => {
                if (isMounted) {
                    setError(err.message || 'Failed to load greeting');
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    return (
        <div className="mb-4">
            {error && (
                <Alert
                    variant="danger"
                    role="alert"
                    dismissible
                    closeLabel="Close alert"
                    onClose={() => setError(null)}
                >
                    {error}
                </Alert>
            )}
            {greeting && <h1 className="text-center">{greeting}</h1>}
        </div>
    );
}

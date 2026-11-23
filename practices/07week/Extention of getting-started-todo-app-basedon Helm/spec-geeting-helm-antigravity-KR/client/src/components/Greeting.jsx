import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

export function Greeting({ onError }) {
    const [greeting, setGreeting] = useState(null);

    useEffect(() => {
        let isMounted = true;
        fetch('/api/greeting')
            .then((res) => {
                if (!res.ok) throw new Error('Greeting service unavailable');
                return res.json();
            })
            .then((data) => {
                if (isMounted) setGreeting(data.greeting);
            })
            .catch((err) => {
                if (onError) onError(err.message);
            });

        return () => {
            isMounted = false;
        };
    }, [onError]);

    if (!greeting) return null;

    return (
        <header className="text-center my-4">
            <h1 className="display-5 fw-bold text-primary">{greeting}</h1>
        </header>
    );
}

Greeting.propTypes = {
    onError: PropTypes.func,
};

export default Greeting;

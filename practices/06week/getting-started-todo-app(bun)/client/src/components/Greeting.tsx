import { useEffect, useState } from 'react';

interface GreetingResponse {
    greeting: string;
}

export function Greeting() {
    const [greeting, setGreeting] = useState<string | null>(null);

    useEffect(() => {
        fetch('/api/greeting')
            .then((res) => res.json() as Promise<GreetingResponse>)
            .then((data) => setGreeting(data.greeting));
    }, []);

    if (!greeting) return null;

    return <h1 className="text-center mb-5">{greeting}</h1>;
}

import { Request, Response } from 'express';

const GREETING = 'Hello world!';

export default async function getGreeting(
    _req: Request,
    res: Response,
): Promise<void> {
    res.send({
        greeting: GREETING,
    });
}

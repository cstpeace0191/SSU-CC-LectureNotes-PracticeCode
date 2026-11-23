import { Request, Response } from 'express';
import db from '../persistence';

export default async function updateItem(
    req: Request,
    res: Response,
): Promise<void> {
    await db.updateItem(req.params.id as string, {
        name: req.body.name,
        completed: req.body.completed,
    });
    const item = await db.getItem(req.params.id as string);
    res.send(item);
}

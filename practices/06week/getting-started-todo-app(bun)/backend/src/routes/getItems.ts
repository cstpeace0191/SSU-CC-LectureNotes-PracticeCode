import { Request, Response } from 'express';
import db from '../persistence';

export default async function getItems(
    _req: Request,
    res: Response,
): Promise<void> {
    const items = await db.getItems();
    res.send(items);
}

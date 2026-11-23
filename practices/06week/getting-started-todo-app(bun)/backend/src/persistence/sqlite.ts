import { Database } from 'bun:sqlite';
import fs from 'fs';
import path from 'path';
import type { Item } from './index';

const location = process.env.SQLITE_DB_LOCATION || '/etc/todos/todo.db';

let db: Database | null = null;

export function init(): Promise<void> {
    const dirName = path.dirname(location);
    if (!fs.existsSync(dirName)) {
        fs.mkdirSync(dirName, { recursive: true });
    }

    return new Promise((acc, rej) => {
        try {
            db = new Database(location);
            if (process.env.NODE_ENV !== 'test') {
                console.log(`Using sqlite database at ${location}`);
            }
            db.run(
                'CREATE TABLE IF NOT EXISTS todo_items (id varchar(36), name varchar(255), completed boolean)',
            );
            acc();
        } catch (err) {
            rej(err);
        }
    });
}

export async function teardown(): Promise<void> {
    if (db) {
        db.close();
        db = null;
    }
}

export async function getItems(): Promise<Item[]> {
    if (!db) throw new Error('Database not initialized');
    const rows = db.query('SELECT * FROM todo_items').all() as any[];
    return rows.map((item) => ({
        id: item.id,
        name: item.name,
        completed: item.completed === 1 || item.completed === true,
    }));
}

export async function getItem(id: string): Promise<Item | undefined> {
    if (!db) throw new Error('Database not initialized');
    const item = db.query('SELECT * FROM todo_items WHERE id=?').get(id) as any;
    if (!item) return undefined;
    return {
        id: item.id,
        name: item.name,
        completed: item.completed === 1 || item.completed === true,
    };
}

export async function storeItem(item: Item): Promise<void> {
    if (!db) throw new Error('Database not initialized');
    db.query(
        'INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)',
    ).run(item.id, item.name, item.completed ? 1 : 0);
}

export async function updateItem(
    id: string,
    item: Partial<Item>,
): Promise<void> {
    if (!db) throw new Error('Database not initialized');
    db.query('UPDATE todo_items SET name=?, completed=? WHERE id = ?').run(
        item.name,
        item.completed ? 1 : 0,
        id,
    );
}

export async function removeItem(id: string): Promise<void> {
    if (!db) throw new Error('Database not initialized');
    db.query('DELETE FROM todo_items WHERE id = ?').run(id);
}

export default {
    init,
    teardown,
    getItems,
    getItem,
    storeItem,
    updateItem,
    removeItem,
};

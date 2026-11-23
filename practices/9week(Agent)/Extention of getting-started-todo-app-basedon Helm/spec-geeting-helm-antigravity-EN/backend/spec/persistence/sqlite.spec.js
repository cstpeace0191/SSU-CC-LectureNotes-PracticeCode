const fs = require('fs');
const path = require('path');

describe('SQLite persistence adapter', () => {
    const testDbPath = path.join(__dirname, 'test-sqlite.db');
    let db;

    beforeEach(async () => {
        process.env.SQLITE_DB_LOCATION = testDbPath;
        if (fs.existsSync(testDbPath)) {
            fs.unlinkSync(testDbPath);
        }
        // Isolate module require
        jest.isolateModules(() => {
            db = require('../../src/persistence/sqlite');
        });
        await db.init();
    });

    afterEach(async () => {
        if (db && db.teardown) {
            await db.teardown();
        }
        if (fs.existsSync(testDbPath)) {
            fs.unlinkSync(testDbPath);
        }
        delete process.env.SQLITE_DB_LOCATION;
    });

    test('stores and retrieves items with normalized boolean completed field', async () => {
        const item1 = {
            id: '11111111-1111-1111-1111-111111111111',
            name: 'Task 1',
            completed: false,
        };
        const item2 = {
            id: '22222222-2222-2222-2222-222222222222',
            name: 'Task 2',
            completed: true,
        };

        await db.storeItem(item1);
        await db.storeItem(item2);

        const items = await db.getItems();
        expect(items).toHaveLength(2);
        expect(items).toContainEqual({
            id: '11111111-1111-1111-1111-111111111111',
            name: 'Task 1',
            completed: false,
        });
        expect(items).toContainEqual({
            id: '22222222-2222-2222-2222-222222222222',
            name: 'Task 2',
            completed: true,
        });
        expect(typeof items[0].completed).toBe('boolean');
        expect(typeof items[1].completed).toBe('boolean');
    });

    test('retrieves a single item by id or undefined if missing', async () => {
        const item = {
            id: '33333333-3333-3333-3333-333333333333',
            name: 'Task 3',
            completed: false,
        };
        await db.storeItem(item);

        const found = await db.getItem('33333333-3333-3333-3333-333333333333');
        expect(found).toEqual({
            id: '33333333-3333-3333-3333-333333333333',
            name: 'Task 3',
            completed: false,
        });
        expect(typeof found.completed).toBe('boolean');

        const missing = await db.getItem('non-existent-id');
        expect(missing).toBeUndefined();
    });

    test('updates an existing item name and completion status', async () => {
        const item = {
            id: '44444444-4444-4444-4444-444444444444',
            name: 'Task 4',
            completed: false,
        };
        await db.storeItem(item);

        await db.updateItem('44444444-4444-4444-4444-444444444444', {
            name: 'Task 4 Updated',
            completed: true,
        });

        const updated = await db.getItem(
            '44444444-4444-4444-4444-444444444444'
        );
        expect(updated).toEqual({
            id: '44444444-4444-4444-4444-444444444444',
            name: 'Task 4 Updated',
            completed: true,
        });
        expect(updated.completed).toBe(true);
    });

    test('removes an item by id', async () => {
        const item = {
            id: '55555555-5555-5555-5555-555555555555',
            name: 'Task 5',
            completed: false,
        };
        await db.storeItem(item);

        await db.removeItem('55555555-5555-5555-5555-555555555555');
        const items = await db.getItems();
        expect(items).toHaveLength(0);

        const found = await db.getItem('55555555-5555-5555-5555-555555555555');
        expect(found).toBeUndefined();
    });

    test('auto-creates nested directories if location directory does not exist', async () => {
        const nestedDir = path.join(__dirname, 'nested', 'sub');
        const nestedDbPath = path.join(nestedDir, 'nested.db');
        process.env.SQLITE_DB_LOCATION = nestedDbPath;

        let nestedDb;
        jest.isolateModules(() => {
            nestedDb = require('../../src/persistence/sqlite');
        });
        await nestedDb.init();
        expect(fs.existsSync(nestedDbPath)).toBe(true);

        await nestedDb.teardown();
        fs.unlinkSync(nestedDbPath);
        fs.rmdirSync(nestedDir);
        fs.rmdirSync(path.join(__dirname, 'nested'));
    });

    test('rejects storeItem on constraint violation', async () => {
        const item = {
            id: 'unique-id',
            name: 'Task Unique',
            completed: false,
        };
        await db.storeItem(item);
        await expect(db.storeItem(item)).rejects.toThrow();
    });

    test('rejects updateItem on constraint violation', async () => {
        const item = {
            id: 'update-constraint-id',
            name: 'Task To Update',
            completed: false,
        };
        await db.storeItem(item);
        await expect(
            db.updateItem('update-constraint-id', {
                name: null,
                completed: false,
            })
        ).rejects.toThrow();
    });

    test('handles teardown when db is already torn down', async () => {
        await db.teardown();
        await expect(db.teardown()).resolves.toBeUndefined();
    });

    test('handles database errors gracefully', async () => {
        await db.teardown();
        // Operations on closed DB should reject
        await expect(db.getItems()).rejects.toThrow();
        await expect(db.getItem('1')).rejects.toThrow();
        await expect(
            db.storeItem({ id: '1', name: 't', completed: false })
        ).rejects.toThrow();
        await expect(
            db.updateItem('1', { name: 't', completed: true })
        ).rejects.toThrow();
        await expect(db.removeItem('1')).rejects.toThrow();
    });

    test('rejects init if db location is a directory', async () => {
        process.env.SQLITE_DB_LOCATION = __dirname;
        let errDb;
        jest.isolateModules(() => {
            errDb = require('../../src/persistence/sqlite');
        });
        await expect(errDb.init()).rejects.toThrow();
    });
});

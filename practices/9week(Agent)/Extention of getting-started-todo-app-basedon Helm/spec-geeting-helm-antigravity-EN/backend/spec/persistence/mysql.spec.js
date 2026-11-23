const waitPort = require('wait-port');
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');

jest.mock('wait-port');
jest.mock('mysql2/promise');

describe('MySQL persistence adapter', () => {
    let mockPool;
    let mockQuery;
    let mockEnd;
    let mysqlAdapter;

    beforeEach(async () => {
        jest.clearAllMocks();
        mockQuery = jest.fn();
        mockEnd = jest.fn().mockResolvedValue();
        mockPool = {
            query: mockQuery,
            end: mockEnd,
        };
        mysql.createPool.mockReturnValue(mockPool);
        waitPort.mockResolvedValue({ open: true });

        process.env.MYSQL_HOST = 'test-host';
        process.env.MYSQL_USER = 'test-user';
        process.env.MYSQL_PASSWORD = 'test-password';
        process.env.MYSQL_DB = 'test-db';

        delete process.env.MYSQL_HOST_FILE;
        delete process.env.MYSQL_USER_FILE;
        delete process.env.MYSQL_PASSWORD_FILE;
        delete process.env.MYSQL_DB_FILE;

        jest.isolateModules(() => {
            mysqlAdapter = require('../../src/persistence/mysql');
        });
        mockQuery.mockResolvedValue([[]]);
        await mysqlAdapter.init();
    });

    afterEach(async () => {
        delete process.env.MYSQL_HOST;
        delete process.env.MYSQL_USER;
        delete process.env.MYSQL_PASSWORD;
        delete process.env.MYSQL_DB;
    });

    test('init calls wait-port, creates pool, and creates todo_items table', async () => {
        mockQuery.mockResolvedValueOnce([[]]);

        await mysqlAdapter.init();

        expect(waitPort).toHaveBeenCalledWith(
            expect.objectContaining({
                host: 'test-host',
            })
        );
        expect(mysql.createPool).toHaveBeenCalledWith(
            expect.objectContaining({
                host: 'test-host',
                user: 'test-user',
                password: 'test-password',
                database: 'test-db',
            })
        );
        expect(mockQuery).toHaveBeenCalledWith(
            expect.stringContaining('CREATE TABLE IF NOT EXISTS todo_items')
        );
    });

    test('supports *_FILE secret files for credentials', async () => {
        const secretPath = path.join(__dirname, 'mock-secret.txt');
        fs.writeFileSync(secretPath, 'secret-password\n');
        process.env.MYSQL_PASSWORD_FILE = secretPath;
        delete process.env.MYSQL_PASSWORD;

        mockQuery.mockResolvedValueOnce([[]]);

        await mysqlAdapter.init();

        expect(mysql.createPool).toHaveBeenCalledWith(
            expect.objectContaining({
                password: 'secret-password',
            })
        );

        fs.unlinkSync(secretPath);
    });

    test('getItems returns records normalized with boolean completed', async () => {
        mockQuery.mockResolvedValueOnce([
            [
                { id: '1', name: 'Item 1', completed: 0 },
                { id: '2', name: 'Item 2', completed: 1 },
            ],
        ]);

        const items = await mysqlAdapter.getItems();

        expect(items).toEqual([
            { id: '1', name: 'Item 1', completed: false },
            { id: '2', name: 'Item 2', completed: true },
        ]);
        expect(typeof items[0].completed).toBe('boolean');
        expect(typeof items[1].completed).toBe('boolean');
    });

    test('getItem returns single item with normalized boolean completed', async () => {
        mockQuery.mockResolvedValueOnce([
            [{ id: '1', name: 'Item 1', completed: 1 }],
        ]);

        const item = await mysqlAdapter.getItem('1');
        expect(item).toEqual({ id: '1', name: 'Item 1', completed: true });

        mockQuery.mockResolvedValueOnce([[]]);
        const missing = await mysqlAdapter.getItem('missing');
        expect(missing).toBeUndefined();
    });

    test('storeItem, updateItem, and removeItem call pool.query with correct params', async () => {
        mockQuery.mockResolvedValue([{}]);

        await mysqlAdapter.storeItem({
            id: 'uuid-1',
            name: 'Task 1',
            completed: false,
        });
        expect(mockQuery).toHaveBeenCalledWith(
            'INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)',
            ['uuid-1', 'Task 1', 0]
        );

        await mysqlAdapter.updateItem('uuid-1', {
            name: 'Task 1 Updated',
            completed: true,
        });
        expect(mockQuery).toHaveBeenCalledWith(
            'UPDATE todo_items SET name = ?, completed = ? WHERE id = ?',
            ['Task 1 Updated', 1, 'uuid-1']
        );

        await mysqlAdapter.removeItem('uuid-1');
        expect(mockQuery).toHaveBeenCalledWith(
            'DELETE FROM todo_items WHERE id = ?',
            ['uuid-1']
        );
    });

    test('teardown gracefully closes pool', async () => {
        mockQuery.mockResolvedValueOnce([[]]);
        await mysqlAdapter.init();
        await mysqlAdapter.teardown();
        expect(mockEnd).toHaveBeenCalledTimes(1);
    });

    test('teardown handles when pool is already closed', async () => {
        await mysqlAdapter.teardown();
        await expect(mysqlAdapter.teardown()).resolves.toBeUndefined();
    });
});

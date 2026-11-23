describe('Dynamic persistence selector', () => {
    const originalEnv = process.env;

    beforeEach(() => {
        jest.resetModules();
        process.env = { ...originalEnv };
        delete process.env.MYSQL_HOST;
        delete process.env.MYSQL_HOST_FILE;
    });

    afterAll(() => {
        process.env = originalEnv;
    });

    test('selects sqlite adapter when MYSQL_HOST is not set', () => {
        const adapter = require('../../src/persistence');
        const sqlite = require('../../src/persistence/sqlite');
        expect(adapter).toBe(sqlite);
    });

    test('selects mysql adapter when MYSQL_HOST is set', () => {
        process.env.MYSQL_HOST = 'mysql-server';
        const adapter = require('../../src/persistence');
        const mysql = require('../../src/persistence/mysql');
        expect(adapter).toBe(mysql);
    });

    test('selects mysql adapter when MYSQL_HOST_FILE is set', () => {
        process.env.MYSQL_HOST_FILE = '/run/secrets/host';
        const adapter = require('../../src/persistence');
        const mysql = require('../../src/persistence/mysql');
        expect(adapter).toBe(mysql);
    });
});

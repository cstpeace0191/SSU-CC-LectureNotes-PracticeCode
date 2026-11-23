const app = require('../src/index');
const db = require('../src/persistence');

jest.mock('../src/persistence', () => ({
    teardown: jest.fn().mockResolvedValue(),
    init: jest.fn().mockResolvedValue(),
}));

describe('Express application and signal shutdown', () => {
    test('routes are registered on express app', () => {
        const router = app.router || app._router;
        const routes = router.stack
            .filter((layer) => layer.route)
            .map((layer) => ({
                path: layer.route.path,
                methods: Object.keys(layer.route.methods),
            }));

        expect(routes).toContainEqual({
            path: '/api/greeting',
            methods: ['get'],
        });
        expect(routes).toContainEqual({
            path: '/api/items',
            methods: ['get'],
        });
        expect(routes).toContainEqual({
            path: '/api/items',
            methods: ['post'],
        });
        expect(routes).toContainEqual({
            path: '/api/items/:id',
            methods: ['put'],
        });
        expect(routes).toContainEqual({
            path: '/api/items/:id',
            methods: ['delete'],
        });
    });

    test('graceful shutdown handler calls db.teardown and exits 0', async () => {
        const originalExit = process.exit;
        process.exit = jest.fn();

        const listeners = process.rawListeners('SIGINT');
        expect(listeners.length).toBeGreaterThan(0);

        const shutdownHandler = listeners[listeners.length - 1];
        await shutdownHandler();

        expect(db.teardown).toHaveBeenCalled();
        expect(process.exit).toHaveBeenCalledWith(0);

        process.exit = originalExit;
    });

    test('graceful shutdown handles teardown error and exits 0', async () => {
        const originalExit = process.exit;
        process.exit = jest.fn();
        db.teardown.mockRejectedValueOnce(new Error('Teardown failure'));

        const listeners = process.rawListeners('SIGTERM');
        const shutdownHandler = listeners[listeners.length - 1];
        await shutdownHandler();

        expect(process.exit).toHaveBeenCalledWith(0);

        process.exit = originalExit;
    });
});

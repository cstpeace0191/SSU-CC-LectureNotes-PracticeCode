const db = require('../../src/persistence');
const addItem = require('../../src/routes/addItem');

jest.mock('../../src/persistence', () => ({
    storeItem: jest.fn(),
}));

describe('POST /api/items route handler', () => {
    let req, res;
    const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    beforeEach(() => {
        req = {
            body: {},
        };
        res = {
            send: jest.fn(),
            status: jest.fn().mockReturnThis(),
            json: jest.fn(),
        };
        jest.clearAllMocks();
    });

    test('successfully stores a valid item and returns it with UUID and completed false', async () => {
        req.body = { name: 'Buy milk' };
        db.storeItem.mockResolvedValue();

        await addItem(req, res);

        expect(db.storeItem).toHaveBeenCalledTimes(1);
        const storedItem = db.storeItem.mock.calls[0][0];

        expect(storedItem.name).toBe('Buy milk');
        expect(storedItem.completed).toBe(false);
        expect(storedItem.id).toMatch(uuidRegex);
        expect(storedItem.id).toHaveLength(36);

        expect(res.send).toHaveBeenCalledWith(storedItem);
    });

    test('returns 400 when name is missing or non-string', async () => {
        req.body = undefined;
        await addItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);

        jest.clearAllMocks();
        req.body = {};
        await addItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.send).toHaveBeenCalledWith({
            error: 'Task name must be a non-empty string up to 255 characters.',
        });

        jest.clearAllMocks();
        req.body = { name: 12345 };
        await addItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(db.storeItem).not.toHaveBeenCalled();
    });

    test('returns 400 when name is empty or whitespace-only', async () => {
        req.body = { name: '   ' };
        await addItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.send).toHaveBeenCalledWith({
            error: 'Task name must be a non-empty string up to 255 characters.',
        });
        expect(db.storeItem).not.toHaveBeenCalled();
    });

    test('returns 400 when name exceeds 255 characters', async () => {
        req.body = { name: 'a'.repeat(256) };
        await addItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.send).toHaveBeenCalledWith({
            error: 'Task name must be a non-empty string up to 255 characters.',
        });
        expect(db.storeItem).not.toHaveBeenCalled();
    });
});

const db = require('../../src/persistence');
const updateItem = require('../../src/routes/updateItem');

jest.mock('../../src/persistence', () => ({
    updateItem: jest.fn(),
    getItem: jest.fn(),
}));

describe('PUT /api/items/:id route handler', () => {
    let req, res;

    beforeEach(() => {
        req = {
            params: { id: 'uuid-123' },
            body: { name: 'Updated task', completed: true },
        };
        res = {
            send: jest.fn(),
            status: jest.fn().mockReturnThis(),
            json: jest.fn(),
        };
        jest.clearAllMocks();
    });

    test('successfully updates item and returns updated item', async () => {
        db.updateItem.mockResolvedValue();
        db.getItem.mockResolvedValue({
            id: 'uuid-123',
            name: 'Updated task',
            completed: true,
        });

        await updateItem(req, res);

        expect(db.updateItem).toHaveBeenCalledWith('uuid-123', {
            name: 'Updated task',
            completed: true,
        });
        expect(res.send).toHaveBeenCalledWith({
            id: 'uuid-123',
            name: 'Updated task',
            completed: true,
        });

        // Test fallback when db.getItem returns null/undefined
        db.getItem.mockResolvedValueOnce(undefined);
        await updateItem(req, res);
        expect(res.send).toHaveBeenCalledWith({
            id: 'uuid-123',
            name: 'Updated task',
            completed: true,
        });
    });

    test('returns 400 when name is missing, invalid or empty/whitespace', async () => {
        req.body = undefined;
        await updateItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);

        jest.clearAllMocks();
        req.body = { completed: true };
        await updateItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);

        jest.clearAllMocks();
        req.body = { name: '   ', completed: true };
        await updateItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);

        jest.clearAllMocks();
        req.body = { name: 'a'.repeat(256), completed: true };
        await updateItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);
    });

    test('returns 400 when completed is not a boolean', async () => {
        req.body = { name: 'Valid task', completed: 'true' };
        await updateItem(req, res);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.send).toHaveBeenCalledWith({
            error: 'Invalid item payload: name (1-255 chars) and boolean completed are required.',
        });
    });
});

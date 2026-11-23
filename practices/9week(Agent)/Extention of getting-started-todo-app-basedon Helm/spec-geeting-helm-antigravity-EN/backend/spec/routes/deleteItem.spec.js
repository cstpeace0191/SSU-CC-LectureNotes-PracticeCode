const db = require('../../src/persistence');
const deleteItem = require('../../src/routes/deleteItem');

jest.mock('../../src/persistence', () => ({
    removeItem: jest.fn(),
}));

describe('DELETE /api/items/:id route handler', () => {
    let req, res;

    beforeEach(() => {
        req = {
            params: { id: 'uuid-123' },
        };
        res = {
            send: jest.fn(),
            sendStatus: jest.fn(),
            status: jest.fn().mockReturnThis(),
            json: jest.fn(),
        };
        jest.clearAllMocks();
    });

    test('calls db.removeItem with item id and returns 200', async () => {
        db.removeItem.mockResolvedValue();

        await deleteItem(req, res);

        expect(db.removeItem).toHaveBeenCalledWith('uuid-123');
        expect(res.sendStatus).toHaveBeenCalledWith(200);
    });
});

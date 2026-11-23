const db = require('../../src/persistence');
const updateItem = require('../../src/routes/updateItem');

jest.mock('../../src/persistence', () => ({
    getItem: jest.fn(),
    updateItem: jest.fn(),
}));

describe('PUT /api/items/:id route handler', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('it updates item completed state and returns updated item', async () => {
        const id = '12345';
        const updatedItem = { id, name: 'Sample Item', completed: true };
        const req = {
            params: { id },
            body: { name: 'Sample Item', completed: true },
        };
        const res = {
            status: jest.fn().mockReturnThis(),
            send: jest.fn(),
        };

        db.updateItem.mockResolvedValue();
        db.getItem.mockResolvedValue(updatedItem);

        await updateItem(req, res);

        expect(db.updateItem).toHaveBeenCalledWith(id, {
            name: 'Sample Item',
            completed: true,
        });
        expect(db.getItem).toHaveBeenCalledWith(id);
        expect(res.send).toHaveBeenCalledWith(updatedItem);
    });

    test('it returns 404 if item does not exist after update', async () => {
        const id = 'non-existent';
        const req = {
            params: { id },
            body: { name: 'Sample Item', completed: true },
        };
        const res = {
            status: jest.fn().mockReturnThis(),
            send: jest.fn(),
        };

        db.updateItem.mockResolvedValue();
        db.getItem.mockResolvedValue(null);

        await updateItem(req, res);

        expect(res.status).toHaveBeenCalledWith(404);
        expect(res.send).toHaveBeenCalledWith({ error: 'Item not found' });
    });
});

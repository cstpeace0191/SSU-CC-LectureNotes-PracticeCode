const db = require('../../src/persistence');
const deleteItem = require('../../src/routes/deleteItem');

jest.mock('../../src/persistence', () => ({
    removeItem: jest.fn(),
    getItem: jest.fn(),
}));

describe('DELETE /api/items/:id route handler', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('it immediately removes item and responds with 200 OK', async () => {
        const id = '12345';
        const req = { params: { id } };
        const res = { sendStatus: jest.fn() };

        db.removeItem.mockResolvedValue();

        await deleteItem(req, res);

        expect(db.removeItem).toHaveBeenCalledTimes(1);
        expect(db.removeItem).toHaveBeenCalledWith(id);
        expect(res.sendStatus).toHaveBeenCalledWith(200);
    });
});

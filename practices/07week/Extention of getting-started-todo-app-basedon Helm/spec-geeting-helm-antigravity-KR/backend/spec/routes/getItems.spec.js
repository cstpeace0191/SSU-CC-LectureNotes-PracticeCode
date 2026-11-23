const db = require('../../src/persistence');
const getItems = require('../../src/routes/getItems');

jest.mock('../../src/persistence', () => ({
    getItems: jest.fn(),
}));

describe('GET /api/items route handler', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('it returns items in FIFO order', async () => {
        const mockItems = [
            { id: '1', name: 'First task', completed: false },
            { id: '2', name: 'Second task', completed: true },
        ];
        const req = {};
        const res = { send: jest.fn() };
        db.getItems.mockResolvedValue(mockItems);

        await getItems(req, res);

        expect(db.getItems).toHaveBeenCalledTimes(1);
        expect(res.send).toHaveBeenCalledWith(mockItems);
    });

    test('it returns empty array when no items exist', async () => {
        const req = {};
        const res = { send: jest.fn() };
        db.getItems.mockResolvedValue([]);

        await getItems(req, res);

        expect(db.getItems).toHaveBeenCalledTimes(1);
        expect(res.send).toHaveBeenCalledWith([]);
    });
});

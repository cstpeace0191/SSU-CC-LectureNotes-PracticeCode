const db = require('../../src/persistence');
const getItems = require('../../src/routes/getItems');

jest.mock('../../src/persistence', () => ({
    getItems: jest.fn(),
}));

describe('GET /api/items route handler', () => {
    let req, res;

    beforeEach(() => {
        req = {};
        res = {
            send: jest.fn(),
            status: jest.fn().mockReturnThis(),
            json: jest.fn(),
        };
        jest.clearAllMocks();
    });

    test('retrieves all items from db and sends response', async () => {
        const mockItems = [
            { id: '1', name: 'Item 1', completed: false },
            { id: '2', name: 'Item 2', completed: true },
        ];
        db.getItems.mockResolvedValue(mockItems);

        await getItems(req, res);

        expect(db.getItems).toHaveBeenCalledTimes(1);
        expect(res.send).toHaveBeenCalledWith(mockItems);
    });
});

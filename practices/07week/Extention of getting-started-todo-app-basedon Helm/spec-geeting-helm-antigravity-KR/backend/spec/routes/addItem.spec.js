const db = require('../../src/persistence');
const addItem = require('../../src/routes/addItem');
const { v4: uuid } = require('uuid');

jest.mock('uuid', () => ({ v4: jest.fn() }));

jest.mock('../../src/persistence', () => ({
    removeItem: jest.fn(),
    storeItem: jest.fn(),
    getItem: jest.fn(),
    getItems: jest.fn(),
}));

describe('POST /api/items route handler', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('it stores item correctly with uuid and completed=false', async () => {
        const id = '550e8400-e29b-41d4-a716-446655440000';
        const name = 'A sample item';
        const req = { body: { name } };
        const res = {
            status: jest.fn().mockReturnThis(),
            send: jest.fn(),
        };

        uuid.mockReturnValue(id);

        await addItem(req, res);

        const expectedItem = { id, name, completed: false };

        expect(db.storeItem).toHaveBeenCalledTimes(1);
        expect(db.storeItem).toHaveBeenCalledWith(expectedItem);
        expect(res.send).toHaveBeenCalledWith(expectedItem);
    });

    test('it rejects empty or whitespace-only name with 400 status', async () => {
        const req = { body: { name: '   ' } };
        const res = {
            status: jest.fn().mockReturnThis(),
            send: jest.fn(),
        };

        await addItem(req, res);

        expect(db.storeItem).not.toHaveBeenCalled();
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.send).toHaveBeenCalledWith({
            error: 'Item name cannot be empty or exceed 255 characters',
        });
    });

    test('it rejects name exceeding 255 characters with 400 status', async () => {
        const longName = 'a'.repeat(256);
        const req = { body: { name: longName } };
        const res = {
            status: jest.fn().mockReturnThis(),
            send: jest.fn(),
        };

        await addItem(req, res);

        expect(db.storeItem).not.toHaveBeenCalled();
        expect(res.status).toHaveBeenCalledWith(400);
    });

    test('it allows duplicate item names and creates a new item with unique ID', async () => {
        const id1 = 'id-1';
        const id2 = 'id-2';
        const name = 'Duplicate Task';
        const res1 = { status: jest.fn().mockReturnThis(), send: jest.fn() };
        const res2 = { status: jest.fn().mockReturnThis(), send: jest.fn() };

        uuid.mockReturnValueOnce(id1).mockReturnValueOnce(id2);

        await addItem({ body: { name } }, res1);
        await addItem({ body: { name } }, res2);

        expect(db.storeItem).toHaveBeenCalledTimes(2);
        expect(res1.send).toHaveBeenCalledWith({
            id: id1,
            name,
            completed: false,
        });
        expect(res2.send).toHaveBeenCalledWith({
            id: id2,
            name,
            completed: false,
        });
    });
});

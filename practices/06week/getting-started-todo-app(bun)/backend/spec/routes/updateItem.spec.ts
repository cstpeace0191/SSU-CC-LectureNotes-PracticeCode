import { test, expect, mock } from 'bun:test';
import db from '../../src/persistence';
import updateItem from '../../src/routes/updateItem';

const ITEM = { id: '1234', name: 'New title', completed: false };

test('it updates items correctly', async () => {
    const originalUpdateItem = db.updateItem;
    const originalGetItem = db.getItem;

    const updateItemMock = mock(async (_id: string, _item: any) => {});
    const getItemMock = mock(async (_id: string) => ITEM);

    db.updateItem = updateItemMock as any;
    db.getItem = getItemMock as any;

    try {
        const req = {
            params: { id: '1234' },
            body: { name: 'New title', completed: false },
        } as any;
        let sentData: any;
        const res = {
            send: mock((data: any) => {
                sentData = data;
            }),
        } as any;

        await updateItem(req, res);

        expect(updateItemMock).toHaveBeenCalledTimes(1);
        expect((updateItemMock.mock.calls as any)[0][0]).toBe('1234');
        expect((updateItemMock.mock.calls as any)[0][1]).toEqual({
            name: 'New title',
            completed: false,
        });

        expect(getItemMock).toHaveBeenCalledTimes(1);
        expect((getItemMock.mock.calls as any)[0][0]).toBe('1234');

        expect(res.send).toHaveBeenCalledTimes(1);
        expect(sentData).toEqual(ITEM);
    } finally {
        db.updateItem = originalUpdateItem;
        db.getItem = originalGetItem;
    }
});

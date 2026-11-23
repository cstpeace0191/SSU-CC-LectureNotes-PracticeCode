import { test, expect, mock } from 'bun:test';
import db from '../../src/persistence';
import addItem from '../../src/routes/addItem';

test('it stores item correctly', async () => {
    const originalStoreItem = db.storeItem;
    const storeItemMock = mock(async (_item: any) => {});
    db.storeItem = storeItemMock as any;

    try {
        const name = 'A sample item';
        const req = { body: { name } } as any;
        let sentData: any;
        const res = {
            send: mock((data: any) => {
                sentData = data;
            }),
        } as any;

        await addItem(req, res);

        expect(storeItemMock).toHaveBeenCalledTimes(1);
        const storedItem = (storeItemMock.mock.calls as any)[0][0] as any;
        expect(storedItem.name).toBe(name);
        expect(storedItem.completed).toBe(false);
        expect(typeof storedItem.id).toBe('string');
        expect(res.send).toHaveBeenCalledTimes(1);
        expect(sentData).toEqual(storedItem);
    } finally {
        db.storeItem = originalStoreItem;
    }
});

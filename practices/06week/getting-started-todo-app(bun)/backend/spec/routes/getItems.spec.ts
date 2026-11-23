import { test, expect, mock } from 'bun:test';
import db from '../../src/persistence';
import getItems from '../../src/routes/getItems';

const ITEMS = [{ id: '12345', name: 'Item 1', completed: false }];

test('it gets items correctly', async () => {
    const originalGetItems = db.getItems;
    const getItemsMock = mock(async () => ITEMS);
    db.getItems = getItemsMock;

    try {
        const req = {} as any;
        let sentData: any;
        const res = {
            send: mock((data: any) => {
                sentData = data;
            }),
        } as any;

        await getItems(req, res);

        expect(getItemsMock).toHaveBeenCalledTimes(1);
        expect(res.send).toHaveBeenCalledTimes(1);
        expect(sentData).toEqual(ITEMS);
    } finally {
        db.getItems = originalGetItems;
    }
});

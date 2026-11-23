import { test, expect, mock } from 'bun:test';
import db from '../../src/persistence';
import deleteItem from '../../src/routes/deleteItem';

test('it removes item correctly', async () => {
    const originalRemoveItem = db.removeItem;
    const removeItemMock = mock(async (_id: string) => {});
    db.removeItem = removeItemMock as any;

    try {
        const req = { params: { id: '12345' } } as any;
        const res = { sendStatus: mock((_code: number) => {}) } as any;

        await deleteItem(req, res);

        expect(removeItemMock).toHaveBeenCalledTimes(1);
        expect((removeItemMock.mock.calls as any)[0][0]).toBe('12345');
        expect(res.sendStatus).toHaveBeenCalledTimes(1);
        expect((res.sendStatus.mock.calls as any)[0][0]).toBe(200);
    } finally {
        db.removeItem = originalRemoveItem;
    }
});

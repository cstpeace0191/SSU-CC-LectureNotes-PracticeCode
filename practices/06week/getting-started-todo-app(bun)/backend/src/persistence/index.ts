export interface Item {
    id: string;
    name: string;
    completed: boolean;
}

export interface PersistenceStore {
    init(): Promise<void>;
    teardown(): Promise<void>;
    getItems(): Promise<Item[]>;
    getItem(id: string): Promise<Item | undefined>;
    storeItem(item: Item): Promise<void>;
    updateItem(id: string, item: Partial<Item>): Promise<void>;
    removeItem(id: string): Promise<void>;
}

import * as mysqlStore from './mysql';
import * as sqliteStore from './sqlite';

const store: PersistenceStore = process.env.MYSQL_HOST
    ? mysqlStore
    : sqliteStore;

export const init = () => store.init();
export const teardown = () => store.teardown();
export const getItems = () => store.getItems();
export const getItem = (id: string) => store.getItem(id);
export const storeItem = (item: Item) => store.storeItem(item);
export const updateItem = (id: string, item: Partial<Item>) =>
    store.updateItem(id, item);
export const removeItem = (id: string) => store.removeItem(id);

export default {
    init,
    teardown,
    getItems,
    getItem,
    storeItem,
    updateItem,
    removeItem,
};

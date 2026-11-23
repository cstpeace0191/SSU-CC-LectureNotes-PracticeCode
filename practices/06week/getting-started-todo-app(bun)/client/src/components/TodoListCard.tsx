import { useCallback, useEffect, useState } from 'react';
import { AddItemForm } from './AddNewItemForm';
import { ItemDisplay } from './ItemDisplay';
import type { Item } from '../types';

export function TodoListCard() {
    const [items, setItems] = useState<Item[] | null>(null);

    useEffect(() => {
        fetch('/api/items')
            .then((r) => r.json() as Promise<Item[]>)
            .then(setItems);
    }, []);

    const onNewItem = useCallback((newItem: Item) => {
        setItems((prevItems) =>
            prevItems ? [...prevItems, newItem] : [newItem],
        );
    }, []);

    const onItemUpdate = useCallback((item: Item) => {
        setItems((prevItems) => {
            if (!prevItems) return prevItems;
            const index = prevItems.findIndex((i) => i.id === item.id);
            return [
                ...prevItems.slice(0, index),
                item,
                ...prevItems.slice(index + 1),
            ];
        });
    }, []);

    const onItemRemoval = useCallback((item: Item) => {
        setItems((prevItems) => {
            if (!prevItems) return prevItems;
            const index = prevItems.findIndex((i) => i.id === item.id);
            return [
                ...prevItems.slice(0, index),
                ...prevItems.slice(index + 1),
            ];
        });
    }, []);

    if (items === null) return <>Loading...</>;

    return (
        <>
            <AddItemForm onNewItem={onNewItem} />
            {items.length === 0 && (
                <p className="text-center">No items yet! Add one above!</p>
            )}
            {items.map((item) => (
                <ItemDisplay
                    key={item.id}
                    item={item}
                    onItemUpdate={onItemUpdate}
                    onItemRemoval={onItemRemoval}
                />
            ))}
        </>
    );
}

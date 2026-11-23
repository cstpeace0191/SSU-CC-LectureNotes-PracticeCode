import { useState, useEffect, useCallback } from 'react';
import { Card, Alert } from 'react-bootstrap';
import AddNewItemForm from './AddNewItemForm.jsx';
import ItemDisplay from './ItemDisplay.jsx';

export default function TodoListCard() {
    const [items, setItems] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        let isMounted = true;
        fetch('/api/items')
            .then(async (response) => {
                if (!response.ok) {
                    throw new Error('Failed to load items');
                }
                return response.json();
            })
            .then((data) => {
                if (isMounted) {
                    setItems(data);
                }
            })
            .catch((err) => {
                if (isMounted) {
                    setError(err.message || 'Failed to load items');
                    setItems([]);
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const onNewItem = useCallback((newItem) => {
        setItems((prev) => (prev ? [...prev, newItem] : [newItem]));
    }, []);

    const onItemUpdate = useCallback((updatedItem) => {
        setItems((prev) =>
            prev
                ? prev.map((item) =>
                      item.id === updatedItem.id ? updatedItem : item
                  )
                : []
        );
    }, []);

    const onItemRemoval = useCallback((removedItem) => {
        setItems((prev) =>
            prev ? prev.filter((item) => item.id !== removedItem.id) : []
        );
    }, []);

    return (
        <Card className="shadow-sm">
            <Card.Body>
                <AddNewItemForm onNewItem={onNewItem} />
                {error && (
                    <Alert
                        variant="danger"
                        role="alert"
                        dismissible
                        closeLabel="Close alert"
                        onClose={() => setError(null)}
                    >
                        {error}
                    </Alert>
                )}
                {items === null && <p className="text-center">Loading...</p>}
                {items !== null && items.length === 0 && (
                    <p className="text-center">No items yet! Add one above!</p>
                )}
                {items !== null &&
                    items.map((item) => (
                        <ItemDisplay
                            key={item.id}
                            item={item}
                            onItemUpdate={onItemUpdate}
                            onItemRemoval={onItemRemoval}
                        />
                    ))}
            </Card.Body>
        </Card>
    );
}

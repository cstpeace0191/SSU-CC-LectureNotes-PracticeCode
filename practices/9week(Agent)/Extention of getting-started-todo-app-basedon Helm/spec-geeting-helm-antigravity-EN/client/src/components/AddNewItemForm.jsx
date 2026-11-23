import { useState } from 'react';
import PropTypes from 'prop-types';
import { Form, InputGroup, Button, Alert } from 'react-bootstrap';

export default function AddNewItemForm({ onNewItem }) {
    const [newItem, setNewItem] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const trimmed = newItem.trim();
        if (!trimmed || submitting) return;

        setSubmitting(true);
        setError(null);

        try {
            const response = await fetch('/api/items', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newItem }),
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(
                    errData.error || `Failed with status ${response.status}`
                );
            }

            const createdItem = await response.json();
            onNewItem(createdItem);
            setNewItem('');
        } catch (err) {
            setError(err.message || 'Failed to add item');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Form onSubmit={handleSubmit} className="mb-3">
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
            <InputGroup>
                <Form.Control
                    type="text"
                    value={newItem}
                    maxLength={255}
                    onChange={(e) => setNewItem(e.target.value)}
                    placeholder="New item..."
                    aria-label="New item"
                />
                <Button
                    type="submit"
                    variant="success"
                    disabled={newItem.trim().length === 0 || submitting}
                >
                    {submitting ? 'Adding...' : 'Add Item'}
                </Button>
            </InputGroup>
        </Form>
    );
}

AddNewItemForm.propTypes = {
    onNewItem: PropTypes.func.isRequired,
};

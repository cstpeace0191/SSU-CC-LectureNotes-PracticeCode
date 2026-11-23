import { useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';

export function AddNewItemForm({ onNewItem, onError }) {
    const [newItem, setNewItem] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const submitNewItem = async (e) => {
        e.preventDefault();
        const trimmed = newItem.trim();
        if (!trimmed || submitting || trimmed.length > 255) return;

        setSubmitting(true);

        try {
            const res = await fetch('/api/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: trimmed }),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.error || 'Failed to add item');
            }

            const item = await res.json();
            onNewItem(item);
            setNewItem('');
        } catch (err) {
            if (onError)
                onError(err.message || 'Error communicating with server');
        } finally {
            setSubmitting(false);
        }
    };

    const isInvalid = !newItem.trim().length || newItem.length > 255;

    return (
        <Form onSubmit={submitNewItem} className="mb-4">
            <Form.Group controlId="newItemInput">
                <Form.Label className="visually-hidden">
                    New task title
                </Form.Label>
                <InputGroup>
                    <Form.Control
                        value={newItem}
                        onChange={(e) => setNewItem(e.target.value)}
                        type="text"
                        placeholder="New Item (최대 255자)"
                        aria-label="New item title"
                        maxLength={255}
                        disabled={submitting}
                        autoComplete="off"
                    />
                    <Button
                        type="submit"
                        variant="success"
                        disabled={isInvalid || submitting}
                        aria-busy={submitting}
                    >
                        {submitting ? 'Adding...' : 'Add Item'}
                    </Button>
                </InputGroup>
            </Form.Group>
        </Form>
    );
}

AddNewItemForm.propTypes = {
    onNewItem: PropTypes.func.isRequired,
    onError: PropTypes.func,
};

export default AddNewItemForm;

import { useState } from 'react';
import PropTypes from 'prop-types';
import { Button, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faCheckSquare,
    faSquare,
    faTrash,
} from '@fortawesome/free-solid-svg-icons';

export default function ItemDisplay({ item, onItemUpdate, onItemRemoval }) {
    const [error, setError] = useState(null);
    const [isUpdating, setIsUpdating] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const toggleCompletion = async () => {
        if (isUpdating || isDeleting) return;
        setIsUpdating(true);
        setError(null);

        try {
            const response = await fetch(`/api/items/${item.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: item.name,
                    completed: !item.completed,
                }),
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(
                    errData.error || `Failed with status ${response.status}`
                );
            }

            const updated = await response.json();
            onItemUpdate(updated);
        } catch (err) {
            setError(err.message || 'Failed to update item');
        } finally {
            setIsUpdating(false);
        }
    };

    const removeItem = async () => {
        if (isUpdating || isDeleting) return;
        setIsDeleting(true);
        setError(null);

        try {
            const response = await fetch(`/api/items/${item.id}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(
                    errData.error || `Failed with status ${response.status}`
                );
            }

            onItemRemoval(item);
        } catch (err) {
            setError(err.message || 'Failed to delete item');
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <div className="mb-2">
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
            <div
                className={`item d-flex align-items-center justify-content-between p-2 rounded ${
                    item.completed ? 'completed' : ''
                }`}
            >
                <div className="d-flex align-items-center gap-2">
                    <Button
                        variant="link"
                        className="text-decoration-none p-0 me-2"
                        onClick={toggleCompletion}
                        disabled={isUpdating || isDeleting}
                        aria-label={`Mark "${item.name}" as ${
                            item.completed ? 'incomplete' : 'complete'
                        }`}
                    >
                        <FontAwesomeIcon
                            icon={item.completed ? faCheckSquare : faSquare}
                            className={
                                item.completed
                                    ? 'text-success'
                                    : 'text-secondary'
                            }
                            size="lg"
                        />
                    </Button>
                    <span className="task-name">{item.name}</span>
                </div>
                <Button
                    variant="link"
                    className="text-danger p-0"
                    onClick={removeItem}
                    disabled={isUpdating || isDeleting}
                    aria-label={`Delete "${item.name}"`}
                >
                    <FontAwesomeIcon icon={faTrash} />
                </Button>
            </div>
        </div>
    );
}

ItemDisplay.propTypes = {
    item: PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        completed: PropTypes.bool.isRequired,
    }).isRequired,
    onItemUpdate: PropTypes.func.isRequired,
    onItemRemoval: PropTypes.func.isRequired,
};

import PropTypes from 'prop-types';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons/faTrash';
import faCheckSquare from '@fortawesome/fontawesome-free-regular/faCheckSquare';
import faSquare from '@fortawesome/fontawesome-free-regular/faSquare';

export function ItemDisplay({ item, onItemUpdate, onItemRemoval, onError }) {
    const toggleCompletion = async () => {
        try {
            const res = await fetch(`/api/items/${item.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: item.name,
                    completed: !item.completed,
                }),
            });

            if (!res.ok) {
                throw new Error('Failed to update task status');
            }

            const updated = await res.json();
            onItemUpdate(updated);
        } catch (err) {
            if (onError) onError(err.message || 'Error updating item');
        }
    };

    const removeItem = async () => {
        try {
            const res = await fetch(`/api/items/${item.id}`, {
                method: 'DELETE',
            });
            if (!res.ok) {
                throw new Error('Failed to delete task');
            }
            onItemRemoval(item);
        } catch (err) {
            if (onError) onError(err.message || 'Error deleting item');
        }
    };

    return (
        <Container
            fluid
            className={`item py-2 px-3 border-bottom ${item.completed ? 'completed' : ''}`}
        >
            <Row className="align-items-center">
                <Col xs={2} sm={1} className="text-center">
                    <Button
                        className="toggles p-1"
                        size="sm"
                        variant="link"
                        onClick={toggleCompletion}
                        aria-label={
                            item.completed
                                ? `Mark "${item.name}" as incomplete`
                                : `Mark "${item.name}" as complete`
                        }
                    >
                        <FontAwesomeIcon
                            icon={item.completed ? faCheckSquare : faSquare}
                            size="lg"
                            className={
                                item.completed
                                    ? 'text-success'
                                    : 'text-secondary'
                            }
                        />
                    </Button>
                </Col>
                <Col xs={8} sm={10} className="name text-break">
                    <span className="item-name">{item.name}</span>
                </Col>
                <Col xs={2} sm={1} className="text-end">
                    <Button
                        size="sm"
                        variant="link"
                        className="delete-btn p-1 text-danger"
                        onClick={removeItem}
                        aria-label={`Delete task: ${item.name}`}
                    >
                        <FontAwesomeIcon icon={faTrash} />
                    </Button>
                </Col>
            </Row>
        </Container>
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
    onError: PropTypes.func,
};

export default ItemDisplay;

import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Spinner from 'react-bootstrap/Spinner';
import { AddNewItemForm } from './AddNewItemForm';
import { ItemDisplay } from './ItemDisplay';

export function TodoListCard({
    items,
    loading,
    onNewItem,
    onItemUpdate,
    onItemRemoval,
    onError,
}) {
    return (
        <Card className="todo-list-card shadow-sm mb-5">
            <Card.Body className="p-4">
                <AddNewItemForm onNewItem={onNewItem} onError={onError} />

                {loading ? (
                    <div className="text-center py-4" role="status">
                        <Spinner animation="border" variant="primary" />
                        <span className="visually-hidden">
                            Loading items...
                        </span>
                        <p className="mt-2 text-muted">Loading items...</p>
                    </div>
                ) : items.length === 0 ? (
                    <p className="text-center text-muted my-4">
                        No items yet! Add one above!
                    </p>
                ) : (
                    <div className="todo-items-list" role="list">
                        {items.map((item) => (
                            <div key={item.id} role="listitem">
                                <ItemDisplay
                                    item={item}
                                    onItemUpdate={onItemUpdate}
                                    onItemRemoval={onItemRemoval}
                                    onError={onError}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </Card.Body>
        </Card>
    );
}

TodoListCard.propTypes = {
    items: PropTypes.arrayOf(
        PropTypes.shape({
            id: PropTypes.string.isRequired,
            name: PropTypes.string.isRequired,
            completed: PropTypes.bool.isRequired,
        }),
    ),
    loading: PropTypes.bool.isRequired,
    onNewItem: PropTypes.func.isRequired,
    onItemUpdate: PropTypes.func.isRequired,
    onItemRemoval: PropTypes.func.isRequired,
    onError: PropTypes.func,
};

export default TodoListCard;

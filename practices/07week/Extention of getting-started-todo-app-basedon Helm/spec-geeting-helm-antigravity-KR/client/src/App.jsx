import { useCallback, useEffect, useState } from 'react';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Alert from 'react-bootstrap/Alert';
import { Greeting } from './components/Greeting';
import { TodoListCard } from './components/TodoListCard';

function App() {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState(null);

    const handleError = useCallback((msg) => {
        setErrorMessage(msg);
    }, []);

    const fetchItems = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/items');
            if (!res.ok) {
                throw new Error('Failed to load todo list from server');
            }
            const data = await res.json();
            setItems(Array.isArray(data) ? data : []);
            setErrorMessage(null);
        } catch (err) {
            handleError(err.message || 'Error communicating with server');
        } finally {
            setLoading(false);
        }
    }, [handleError]);

    useEffect(() => {
        fetchItems();
    }, [fetchItems]);

    const handleNewItem = useCallback((newItem) => {
        setItems((prevItems) => [...prevItems, newItem]);
        setErrorMessage(null);
    }, []);

    const handleItemUpdate = useCallback((updatedItem) => {
        setItems((prevItems) =>
            prevItems.map((item) =>
                item.id === updatedItem.id ? updatedItem : item,
            ),
        );
        setErrorMessage(null);
    }, []);

    const handleItemRemoval = useCallback((removedItem) => {
        setItems((prevItems) =>
            prevItems.filter((item) => item.id !== removedItem.id),
        );
        setErrorMessage(null);
    }, []);

    return (
        <main>
            <Container>
                <Row className="justify-content-center">
                    <Col xs={12} md={8} lg={6}>
                        {errorMessage && (
                            <Alert
                                variant="danger"
                                dismissible
                                onClose={() => setErrorMessage(null)}
                                className="mt-3"
                                role="alert"
                            >
                                <strong>오류 안내:</strong> {errorMessage}
                            </Alert>
                        )}
                        <Greeting onError={handleError} />
                        <TodoListCard
                            items={items}
                            loading={loading}
                            onNewItem={handleNewItem}
                            onItemUpdate={handleItemUpdate}
                            onItemRemoval={handleItemRemoval}
                            onError={handleError}
                        />
                    </Col>
                </Row>
            </Container>
        </main>
    );
}

export default App;

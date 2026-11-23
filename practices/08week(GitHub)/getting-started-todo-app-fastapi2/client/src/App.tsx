import { useState } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import { TodoListCard } from './components/TodoListCard';
import { Greeting } from './components/Greeting';
import { Login } from './components/Login';

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    return (
        <Container>
            <Row>
                <Col md={{ offset: 3, span: 6 }}>
                    {isLoggedIn ? (
                        <>
                            <Greeting />
                            <TodoListCard />
                        </>
                    ) : (
                        <Login onLogin={() => setIsLoggedIn(true)} />
                    )}
                </Col>
            </Row>
        </Container>
    );
}

export default App;

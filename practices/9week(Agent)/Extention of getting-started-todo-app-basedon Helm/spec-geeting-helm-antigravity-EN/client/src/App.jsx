import { Container, Row, Col } from 'react-bootstrap';
import Greeting from './components/Greeting.jsx';
import TodoListCard from './components/TodoListCard.jsx';

export default function App() {
    return (
        <Container className="py-5">
            <Row className="justify-content-center">
                <Col md={8} lg={6}>
                    <Greeting />
                    <TodoListCard />
                </Col>
            </Row>
        </Container>
    );
}

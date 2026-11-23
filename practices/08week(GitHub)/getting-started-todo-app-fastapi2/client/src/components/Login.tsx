import { useState } from 'react';
import type { FormEvent } from 'react';
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import Alert from 'react-bootstrap/Alert';

const VALID_ACCOUNT = 'SCC';
const VALID_PASSWORD = '


';

interface LoginProps {
    onLogin: () => void;
}

export function Login({ onLogin }: LoginProps) {
    const [account, setAccount] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    function handleSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        if (account === VALID_ACCOUNT && password === VALID_PASSWORD) {
            setError('');
            onLogin();
        } else {
            setError('계정 또는 암호가 올바르지 않습니다.');
        }
    }

    return (
        <Card className="mt-5">
            <Card.Body>
                <Card.Title className="text-center mb-4">Login</Card.Title>
                {error && <Alert variant="danger">{error}</Alert>}
                <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-3" controlId="loginAccount">
                        <Form.Label>계정</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="계정을 입력하세요"
                            value={account}
                            onChange={(e) => setAccount(e.target.value)}
                            autoComplete="username"
                            required
                        />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="loginPassword">
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="Password를 입력하세요"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete="current-password"
                            required
                        />
                    </Form.Group>
                    <div className="d-grid">
                        <Button type="submit" variant="primary">
                            로그인
                        </Button>
                    </div>
                </Form>
            </Card.Body>
        </Card>
    );
}


import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AddNewItemForm from '../components/AddNewItemForm.jsx';

describe('AddNewItemForm component', () => {
    let onNewItemMock;

    beforeEach(() => {
        onNewItemMock = vi.fn();
        vi.restoreAllMocks();
    });

    it('renders input with maxLength 255 and disabled submit button when input is empty or whitespace', async () => {
        const user = userEvent.setup();
        render(<AddNewItemForm onNewItem={onNewItemMock} />);

        const input = screen.getByPlaceholderText(/new item/i);
        const submitButton = screen.getByRole('button', { name: /add item/i });

        expect(input).toHaveAttribute('maxlength', '255');
        expect(submitButton).toBeDisabled();

        await user.type(input, '   ');
        expect(submitButton).toBeDisabled();

        await user.clear(input);
        await user.type(input, 'Valid task');
        expect(submitButton).toBeEnabled();
    });

    it('submits valid task, shows "Adding..." state, calls onNewItem and clears input on success', async () => {
        const user = userEvent.setup();
        const createdItem = {
            id: 'uuid-123',
            name: 'Valid task',
            completed: false,
        };

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => createdItem,
        });

        render(<AddNewItemForm onNewItem={onNewItemMock} />);

        const input = screen.getByPlaceholderText(/new item/i);
        const submitButton = screen.getByRole('button', { name: /add item/i });

        await user.type(input, 'Valid task');
        await user.click(submitButton);

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/items', {
                method: 'POST',
                body: JSON.stringify({ name: 'Valid task' }),
                headers: { 'Content-Type': 'application/json' },
            });
            expect(onNewItemMock).toHaveBeenCalledWith(createdItem);
            expect(input).toHaveValue('');
        });
    });

    it('preserves input text and renders dismissible alert on error', async () => {
        const user = userEvent.setup();

        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
            json: async () => ({ error: 'Internal Server Error' }),
        });

        render(<AddNewItemForm onNewItem={onNewItemMock} />);

        const input = screen.getByPlaceholderText(/new item/i);
        const submitButton = screen.getByRole('button', { name: /add item/i });

        await user.type(input, 'Important task');
        await user.click(submitButton);

        const alert = await screen.findByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(input).toHaveValue('Important task');
        expect(onNewItemMock).not.toHaveBeenCalled();

        // Dismiss the alert
        const closeButton = screen.getByLabelText(/close alert/i);
        await user.click(closeButton);
        await waitFor(() => {
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
        });
    });
});

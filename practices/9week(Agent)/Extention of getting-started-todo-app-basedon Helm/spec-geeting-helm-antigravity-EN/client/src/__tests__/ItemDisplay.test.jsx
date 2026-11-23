import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ItemDisplay from '../components/ItemDisplay.jsx';

describe('ItemDisplay component', () => {
    let onItemUpdateMock, onItemRemovalMock;

    beforeEach(() => {
        onItemUpdateMock = vi.fn();
        onItemRemovalMock = vi.fn();
        vi.restoreAllMocks();
    });

    it('renders incomplete item with toggle button and accessible aria-label', async () => {
        const item = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: false,
        };

        render(
            <ItemDisplay
                item={item}
                onItemUpdate={onItemUpdateMock}
                onItemRemoval={onItemRemovalMock}
            />
        );

        expect(screen.getByText('Buy milk')).toBeInTheDocument();
        const toggleBtn = screen.getByRole('button', {
            name: /mark "buy milk" as complete/i,
        });
        expect(toggleBtn).toBeInTheDocument();
        expect(screen.getByText('Buy milk').closest('.item')).not.toHaveClass(
            'completed'
        );
    });

    it('toggles completion status on click, calls PUT /api/items/:id, and calls onItemUpdate', async () => {
        const user = userEvent.setup();
        const item = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: false,
        };
        const updatedItem = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: true,
        };

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => updatedItem,
        });

        render(
            <ItemDisplay
                item={item}
                onItemUpdate={onItemUpdateMock}
                onItemRemoval={onItemRemovalMock}
            />
        );

        const toggleBtn = screen.getByRole('button', {
            name: /mark "buy milk" as complete/i,
        });
        await user.click(toggleBtn);

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/items/uuid-1', {
                method: 'PUT',
                body: JSON.stringify({ name: 'Buy milk', completed: true }),
                headers: { 'Content-Type': 'application/json' },
            });
            expect(onItemUpdateMock).toHaveBeenCalledWith(updatedItem);
        });
    });

    it('shows completed styling and toggles back to incomplete when completed is true', async () => {
        const user = userEvent.setup();
        const item = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: true,
        };
        const revertedItem = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: false,
        };

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => revertedItem,
        });

        render(
            <ItemDisplay
                item={item}
                onItemUpdate={onItemUpdateMock}
                onItemRemoval={onItemRemovalMock}
            />
        );

        expect(screen.getByText('Buy milk').closest('.item')).toHaveClass(
            'completed'
        );
        const toggleBtn = screen.getByRole('button', {
            name: /mark "buy milk" as incomplete/i,
        });
        await user.click(toggleBtn);

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/items/uuid-1', {
                method: 'PUT',
                body: JSON.stringify({ name: 'Buy milk', completed: false }),
                headers: { 'Content-Type': 'application/json' },
            });
            expect(onItemUpdateMock).toHaveBeenCalledWith(revertedItem);
        });
    });

    it('displays dismissible error alert when PUT request fails', async () => {
        const user = userEvent.setup();
        const item = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: false,
        };

        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
        });

        render(
            <ItemDisplay
                item={item}
                onItemUpdate={onItemUpdateMock}
                onItemRemoval={onItemRemovalMock}
            />
        );

        const toggleBtn = screen.getByRole('button', {
            name: /mark "buy milk" as complete/i,
        });
        await user.click(toggleBtn);

        const alert = await screen.findByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(onItemUpdateMock).not.toHaveBeenCalled();

        const closeButton = screen.getByLabelText(/close alert/i);
        await user.click(closeButton);
        await waitFor(() => {
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
        });
    });

    it('deletes item on delete button click and calls onItemRemoval', async () => {
        const user = userEvent.setup();
        const item = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: false,
        };

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
        });

        render(
            <ItemDisplay
                item={item}
                onItemUpdate={onItemUpdateMock}
                onItemRemoval={onItemRemovalMock}
            />
        );

        const deleteBtn = screen.getByRole('button', {
            name: /delete "buy milk"/i,
        });
        await user.click(deleteBtn);

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/items/uuid-1', {
                method: 'DELETE',
            });
            expect(onItemRemovalMock).toHaveBeenCalledWith(item);
        });
    });

    it('displays dismissible error alert when DELETE request fails', async () => {
        const user = userEvent.setup();
        const item = {
            id: 'uuid-1',
            name: 'Buy milk',
            completed: false,
        };

        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
        });

        render(
            <ItemDisplay
                item={item}
                onItemUpdate={onItemUpdateMock}
                onItemRemoval={onItemRemovalMock}
            />
        );

        const deleteBtn = screen.getByRole('button', {
            name: /delete "buy milk"/i,
        });
        await user.click(deleteBtn);

        const alert = await screen.findByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(onItemRemovalMock).not.toHaveBeenCalled();

        const closeButton = screen.getByLabelText(/close alert/i);
        await user.click(closeButton);
        await waitFor(() => {
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
        });
    });
});

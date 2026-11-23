import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import TodoListCard from '../components/TodoListCard.jsx';

describe('TodoListCard component', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('shows "Loading..." indicator initially and "No items yet! Add one above!" when empty', async () => {
        global.fetch = vi.fn().mockImplementation(() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve({
                        ok: true,
                        json: async () => [],
                    });
                }, 50);
            });
        });

        render(<TodoListCard />);

        expect(screen.getByText(/loading\.\.\./i)).toBeInTheDocument();

        await waitFor(() => {
            expect(
                screen.getByText(/no items yet! add one above!/i)
            ).toBeInTheDocument();
        });
    });

    it('renders list of fetched items and appends newly added items', async () => {
        const mockItems = [
            { id: '1', name: 'Task One', completed: false },
            { id: '2', name: 'Task Two', completed: true },
        ];

        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockItems,
        });

        render(<TodoListCard />);

        await waitFor(() => {
            expect(screen.getByText('Task One')).toBeInTheDocument();
            expect(screen.getByText('Task Two')).toBeInTheDocument();
        });
    });

    it('displays dismissible error alert when fetching items fails', async () => {
        const user = userEvent.setup();
        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
        });

        render(<TodoListCard />);

        const alert = await screen.findByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent(/failed to load items/i);

        // Dismiss alert
        const closeButton = screen.getByLabelText(/close alert/i);
        await user.click(closeButton);
        await waitFor(() => {
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
        });
    });

    it('transitions to empty message when the last item is removed', async () => {
        const user = userEvent.setup();
        const singleItem = [{ id: '1', name: 'Only Task', completed: false }];

        global.fetch = vi.fn().mockImplementation((url, options) => {
            if (!options || options.method === undefined) {
                return Promise.resolve({
                    ok: true,
                    json: async () => singleItem,
                });
            }
            if (options.method === 'DELETE') {
                return Promise.resolve({
                    ok: true,
                });
            }
            return Promise.resolve({ ok: true });
        });

        render(<TodoListCard />);

        await waitFor(() => {
            expect(screen.getByText('Only Task')).toBeInTheDocument();
        });

        const deleteBtn = screen.getByRole('button', {
            name: /delete "only task"/i,
        });
        await user.click(deleteBtn);

        await waitFor(() => {
            expect(
                screen.getByText(/no items yet! add one above!/i)
            ).toBeInTheDocument();
            expect(screen.queryByText('Only Task')).not.toBeInTheDocument();
        });
    });
});

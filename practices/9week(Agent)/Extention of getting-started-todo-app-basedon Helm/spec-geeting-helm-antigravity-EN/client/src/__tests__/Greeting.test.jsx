import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Greeting from '../components/Greeting.jsx';

describe('Greeting component', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('fetches and renders "Hello world!" heading banner', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ greeting: 'Hello world!' }),
        });

        render(<Greeting />);

        await waitFor(() => {
            expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
                'Hello world!'
            );
        });
    });

    it('displays dismissible error alert when greeting fetch fails', async () => {
        const user = userEvent.setup();
        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
        });

        render(<Greeting />);

        const alert = await screen.findByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent(/failed to load greeting/i);

        const closeButton = screen.getByLabelText(/close alert/i);
        await user.click(closeButton);
        await waitFor(() => {
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
        });
    });
});

import { render, screen, waitFor } from '@testing-library/react';
import axe from 'axe-core';
import { describe, it, expect, vi } from 'vitest';
import App from '../App.jsx';
import Greeting from '../components/Greeting.jsx';
import AddNewItemForm from '../components/AddNewItemForm.jsx';
import ItemDisplay from '../components/ItemDisplay.jsx';

describe('Accessibility (WCAG 2.1 Level AA) Audits', () => {
    it('has no critical or serious a11y violations in AddNewItemForm', async () => {
        const { container } = render(<AddNewItemForm onNewItem={() => {}} />);
        const results = await axe.run(container);
        const violations = results.violations.filter(
            (v) => v.impact === 'critical' || v.impact === 'serious'
        );
        expect(violations).toEqual([]);
    });

    it('has no critical or serious a11y violations in ItemDisplay', async () => {
        const item = {
            id: '1',
            name: 'Sample task',
            completed: false,
        };
        const { container } = render(
            <ItemDisplay
                item={item}
                onItemUpdate={() => {}}
                onItemRemoval={() => {}}
            />
        );
        const results = await axe.run(container);
        const violations = results.violations.filter(
            (v) => v.impact === 'critical' || v.impact === 'serious'
        );
        expect(violations).toEqual([]);
    });

    it('has no critical or serious a11y violations in Greeting', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ greeting: 'Hello world!' }),
        });

        const { container } = render(<Greeting />);
        await waitFor(() => {
            expect(
                screen.getByRole('heading', { level: 1 })
            ).toBeInTheDocument();
        });

        const results = await axe.run(container);
        const violations = results.violations.filter(
            (v) => v.impact === 'critical' || v.impact === 'serious'
        );
        expect(violations).toEqual([]);
    });

    it('has no critical or serious a11y violations in App', async () => {
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('greeting')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ greeting: 'Hello world!' }),
                });
            }
            return Promise.resolve({
                ok: true,
                json: async () => [
                    { id: '1', name: 'Task 1', completed: false },
                ],
            });
        });

        const { container } = render(<App />);
        await waitFor(() => {
            expect(
                screen.getByRole('heading', { level: 1 })
            ).toBeInTheDocument();
            expect(screen.getByText('Task 1')).toBeInTheDocument();
        });

        const results = await axe.run(container);
        const violations = results.violations.filter(
            (v) => v.impact === 'critical' || v.impact === 'serious'
        );
        expect(violations).toEqual([]);
    });
});

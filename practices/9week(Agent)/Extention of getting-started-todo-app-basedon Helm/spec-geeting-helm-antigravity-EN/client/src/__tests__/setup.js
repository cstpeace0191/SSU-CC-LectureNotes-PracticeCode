import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
    cleanup();
    if (global.fetch && typeof global.fetch.mockClear === 'function') {
        global.fetch.mockClear();
    }
});

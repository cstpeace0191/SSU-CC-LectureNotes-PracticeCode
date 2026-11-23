import { test, expect } from 'bun:test';

test('client environment runs on bun', () => {
    expect(typeof Bun).toBe('object');
});


const getGreeting = require('../../src/routes/getGreeting');

describe('GET /api/greeting route handler', () => {
    test('it returns Hello world! greeting', async () => {
        const req = {};
        const res = { send: jest.fn() };

        await getGreeting(req, res);

        expect(res.send).toHaveBeenCalledTimes(1);
        expect(res.send).toHaveBeenCalledWith({ greeting: 'Hello world!' });
    });
});

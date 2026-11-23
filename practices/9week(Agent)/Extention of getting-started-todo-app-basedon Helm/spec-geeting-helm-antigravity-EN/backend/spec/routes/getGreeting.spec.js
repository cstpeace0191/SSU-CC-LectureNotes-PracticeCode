const getGreeting = require('../../src/routes/getGreeting');

describe('GET /api/greeting route handler', () => {
    let req, res;

    beforeEach(() => {
        req = {};
        res = {
            send: jest.fn(),
            json: jest.fn(),
        };
    });

    test('returns greeting object { greeting: "Hello world!" }', async () => {
        await getGreeting(req, res);
        expect(res.send).toHaveBeenCalledWith({ greeting: 'Hello world!' });
    });
});

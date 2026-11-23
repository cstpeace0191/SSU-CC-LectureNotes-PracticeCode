const db = require('../persistence');
const { v4: uuid } = require('uuid');

module.exports = async (req, res) => {
    const { name } = req.body || {};

    if (
        typeof name !== 'string' ||
        name.trim().length === 0 ||
        name.length > 255
    ) {
        return res.status(400).send({
            error: 'Task name must be a non-empty string up to 255 characters.',
        });
    }

    const item = {
        id: uuid(),
        name,
        completed: false,
    };

    await db.storeItem(item);
    res.send(item);
};

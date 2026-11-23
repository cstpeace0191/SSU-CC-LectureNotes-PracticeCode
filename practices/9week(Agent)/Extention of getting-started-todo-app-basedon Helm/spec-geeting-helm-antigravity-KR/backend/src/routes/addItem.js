const db = require('../persistence');
const { v4: uuid } = require('uuid');

module.exports = async (req, res) => {
    const rawName = req.body && req.body.name;

    if (!rawName || typeof rawName !== 'string') {
        return res.status(400).send({
            error: 'Item name cannot be empty or exceed 255 characters',
        });
    }

    const name = rawName.trim();
    if (name.length === 0 || name.length > 255) {
        return res.status(400).send({
            error: 'Item name cannot be empty or exceed 255 characters',
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

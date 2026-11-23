const db = require('../persistence');

module.exports = async (req, res) => {
    try {
        const items = await db.getItems();
        res.send(items);
    } catch (err) {
        res.status(500).send({ error: 'Failed to retrieve items' });
    }
};

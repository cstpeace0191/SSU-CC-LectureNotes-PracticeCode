const db = require('../persistence');

module.exports = async (req, res) => {
    try {
        await db.removeItem(req.params.id);
        res.sendStatus(200);
    } catch (err) {
        res.status(500).send({ error: 'Failed to delete item' });
    }
};

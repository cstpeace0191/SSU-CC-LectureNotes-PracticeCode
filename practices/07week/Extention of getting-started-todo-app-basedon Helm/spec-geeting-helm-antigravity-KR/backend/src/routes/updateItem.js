const db = require('../persistence');

module.exports = async (req, res) => {
    try {
        const id = req.params.id;
        const name = req.body.name;
        const completed = req.body.completed;

        await db.updateItem(id, { name, completed });
        const item = await db.getItem(id);

        if (!item) {
            return res.status(404).send({ error: 'Item not found' });
        }

        res.send(item);
    } catch (err) {
        res.status(500).send({ error: 'Failed to update item' });
    }
};

const db = require('../persistence');

module.exports = async (req, res) => {
    const { name, completed } = req.body || {};
    const { id } = req.params;

    if (
        typeof name !== 'string' ||
        name.trim().length === 0 ||
        name.length > 255 ||
        typeof completed !== 'boolean'
    ) {
        return res.status(400).send({
            error: 'Invalid item payload: name (1-255 chars) and boolean completed are required.',
        });
    }

    await db.updateItem(id, { name, completed });
    const updated = await db.getItem(id);
    res.send(updated || { id, name, completed });
};

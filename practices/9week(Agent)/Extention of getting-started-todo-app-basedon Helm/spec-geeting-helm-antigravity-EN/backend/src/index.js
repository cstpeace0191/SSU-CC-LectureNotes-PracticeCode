const express = require('express');
const fs = require('fs');
const path = require('path');
const db = require('./persistence');

const app = express();
app.use(express.json());

const staticDir = fs.existsSync(path.join(__dirname, '../static'))
    ? path.join(__dirname, '../static')
    : path.join(__dirname, 'static');

app.use(express.static(staticDir));

app.get('/api/greeting', require('./routes/getGreeting'));
app.get('/api/items', require('./routes/getItems'));
app.post('/api/items', require('./routes/addItem'));
app.put('/api/items/:id', require('./routes/updateItem'));
app.delete('/api/items/:id', require('./routes/deleteItem'));

const gracefulShutdown = () =>
    db
        .teardown()
        .catch(() => {})
        .then(() => process.exit(0));

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);
process.on('SIGUSR2', gracefulShutdown);

const PORT = process.env.PORT || 3000;

if (require.main === module) {
    db.init()
        .then(() => {
            app.listen(PORT, () => {
                console.log(`Listening on port ${PORT}`);
            });
        })
        .catch((err) => {
            console.error('Failed to initialize database:', err);
            process.exit(1);
        });
}

module.exports = app;

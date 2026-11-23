const waitPort = require('wait-port');
const fs = require('fs');
const mysql = require('mysql2/promise');

let pool;

function getEnv(key) {
    const fileKey = key + '_FILE';
    if (process.env[fileKey] && fs.existsSync(process.env[fileKey])) {
        return fs.readFileSync(process.env[fileKey], 'utf8').trim();
    }
    return process.env[key];
}

async function init() {
    const host = getEnv('MYSQL_HOST');
    const user = getEnv('MYSQL_USER');
    const password = getEnv('MYSQL_PASSWORD');
    const database = getEnv('MYSQL_DB');

    await waitPort({
        host,
        port: 3306,
        timeout: 15000,
        output: 'silent',
    });

    pool = mysql.createPool({
        host,
        user,
        password,
        database,
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0,
    });

    await pool.query(
        `CREATE TABLE IF NOT EXISTS todo_items (
            id varchar(36) PRIMARY KEY,
            name varchar(255) NOT NULL,
            completed boolean NOT NULL DEFAULT 0
        ) DEFAULT CHARSET utf8mb4`
    );
}

async function teardown() {
    if (pool) {
        await pool.end();
        pool = null;
    }
}

async function getItems() {
    const [rows] = await pool.query('SELECT * FROM todo_items');
    return rows.map((row) => ({
        ...row,
        completed: Boolean(row.completed),
    }));
}

async function getItem(id) {
    const [rows] = await pool.query('SELECT * FROM todo_items WHERE id = ?', [
        id,
    ]);
    if (!rows || rows.length === 0) {
        return undefined;
    }
    return {
        ...rows[0],
        completed: Boolean(rows[0].completed),
    };
}

async function storeItem(item) {
    await pool.query(
        'INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)',
        [item.id, item.name, item.completed ? 1 : 0]
    );
}

async function updateItem(id, item) {
    await pool.query(
        'UPDATE todo_items SET name = ?, completed = ? WHERE id = ?',
        [item.name, item.completed ? 1 : 0, id]
    );
}

async function removeItem(id) {
    await pool.query('DELETE FROM todo_items WHERE id = ?', [id]);
}

module.exports = {
    init,
    teardown,
    getItems,
    getItem,
    storeItem,
    updateItem,
    removeItem,
};

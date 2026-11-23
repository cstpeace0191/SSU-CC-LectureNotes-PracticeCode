module.exports =
    Boolean(process.env.MYSQL_HOST) || Boolean(process.env.MYSQL_HOST_FILE)
        ? require('./mysql')
        : require('./sqlite');

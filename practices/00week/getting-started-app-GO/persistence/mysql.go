package persistence

import (
	"database/sql"
	"fmt"
	"log"
	"net"
	"os"
	"strings"
	"time"

	_ "github.com/go-sql-driver/mysql"
)

type mysqlDB struct {
	db *sql.DB
}

func readSecretOrEnv(envVar, fileVar string) string {
	filePath := os.Getenv(fileVar)
	if filePath != "" {
		if data, err := os.ReadFile(filePath); err == nil {
			return strings.TrimSpace(string(data))
		}
	}
	return os.Getenv(envVar)
}

// NewMySQLDB initializes a MySQL database connection with retry/wait logic
func NewMySQLDB() (DB, error) {
	host := readSecretOrEnv("MYSQL_HOST", "MYSQL_HOST_FILE")
	user := readSecretOrEnv("MYSQL_USER", "MYSQL_USER_FILE")
	password := readSecretOrEnv("MYSQL_PASSWORD", "MYSQL_PASSWORD_FILE")
	database := readSecretOrEnv("MYSQL_DB", "MYSQL_DB_FILE")

	if host == "" {
		host = "localhost"
	}
	if user == "" {
		user = "root"
	}
	if database == "" {
		database = "todos"
	}

	// Wait for MySQL port 3306 to be ready (up to 15 seconds)
	addr := host
	if !strings.Contains(host, ":") {
		addr = net.JoinHostPort(host, "3306")
	}

	log.Printf("Waiting for MySQL at %s...", addr)
	deadline := time.Now().Add(15 * time.Second)
	for {
		conn, err := net.DialTimeout("tcp", addr, 2*time.Second)
		if err == nil {
			conn.Close()
			break
		}
		if time.Now().After(deadline) {
			return nil, fmt.Errorf("timeout waiting for mysql port: %w", err)
		}
		time.Sleep(500 * time.Millisecond)
	}

	dsn := fmt.Sprintf("%s:%s@tcp(%s)/%s?charset=utf8mb4&parseTime=True&loc=Local",
		user, password, addr, database)

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open mysql connection: %w", err)
	}

	db.SetMaxOpenConns(5)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Minute * 5)

	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to ping mysql: %w", err)
	}

	schema := `CREATE TABLE IF NOT EXISTS todo_items (
		id VARCHAR(36) PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		completed BOOLEAN NOT NULL DEFAULT 0
	) DEFAULT CHARSET utf8mb4;`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create mysql table: %w", err)
	}

	log.Printf("Connected to mysql db at host %s", host)
	return &mysqlDB{db: db}, nil
}

func (m *mysqlDB) GetItems() ([]Item, error) {
	rows, err := m.db.Query("SELECT id, name, completed FROM todo_items")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	items := make([]Item, 0)
	for rows.Next() {
		var item Item
		var completed bool
		if err := rows.Scan(&item.ID, &item.Name, &completed); err != nil {
			return nil, err
		}
		item.Completed = completed
		items = append(items, item)
	}

	return items, rows.Err()
}

func (m *mysqlDB) GetItem(id string) (*Item, error) {
	row := m.db.QueryRow("SELECT id, name, completed FROM todo_items WHERE id = ?", id)

	var item Item
	var completed bool
	if err := row.Scan(&item.ID, &item.Name, &completed); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	item.Completed = completed
	return &item, nil
}

func (m *mysqlDB) StoreItem(item Item) error {
	_, err := m.db.Exec("INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)", item.ID, item.Name, item.Completed)
	return err
}

func (m *mysqlDB) UpdateItem(id string, item Item) error {
	_, err := m.db.Exec("UPDATE todo_items SET name = ?, completed = ? WHERE id = ?", item.Name, item.Completed, id)
	return err
}

func (m *mysqlDB) RemoveItem(id string) error {
	_, err := m.db.Exec("DELETE FROM todo_items WHERE id = ?", id)
	return err
}

func (m *mysqlDB) Close() error {
	return m.db.Close()
}

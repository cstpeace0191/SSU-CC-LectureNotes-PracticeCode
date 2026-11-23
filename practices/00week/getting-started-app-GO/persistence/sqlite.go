package persistence

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"

	_ "modernc.org/sqlite"
)

type sqliteDB struct {
	db *sql.DB
}

// NewSQLiteDB initializes a SQLite database connection
func NewSQLiteDB() (DB, error) {
	location := os.Getenv("SQLITE_DB_LOCATION")
	if location == "" {
		if runtime.GOOS == "windows" {
			location = filepath.Join(".", "todo.db")
		} else {
			location = "/etc/todos/todo.db"
		}
	}

	dirName := filepath.Dir(location)
	if err := os.MkdirAll(dirName, 0755); err != nil {
		return nil, fmt.Errorf("failed to create db directory: %w", err)
	}

	db, err := sql.Open("sqlite", location)
	if err != nil {
		return nil, fmt.Errorf("failed to open sqlite db: %w", err)
	}

	if os.Getenv("NODE_ENV") != "test" {
		log.Printf("Using sqlite database at %s", location)
	}

	schema := `CREATE TABLE IF NOT EXISTS todo_items (
		id VARCHAR(36) PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		completed BOOLEAN NOT NULL DEFAULT 0
	);`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create table: %w", err)
	}

	return &sqliteDB{db: db}, nil
}

func (s *sqliteDB) GetItems() ([]Item, error) {
	rows, err := s.db.Query("SELECT id, name, completed FROM todo_items")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	items := make([]Item, 0)
	for rows.Next() {
		var item Item
		var completed int
		if err := rows.Scan(&item.ID, &item.Name, &completed); err != nil {
			return nil, err
		}
		item.Completed = (completed == 1)
		items = append(items, item)
	}

	return items, rows.Err()
}

func (s *sqliteDB) GetItem(id string) (*Item, error) {
	row := s.db.QueryRow("SELECT id, name, completed FROM todo_items WHERE id = ?", id)

	var item Item
	var completed int
	if err := row.Scan(&item.ID, &item.Name, &completed); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	item.Completed = (completed == 1)
	return &item, nil
}

func (s *sqliteDB) StoreItem(item Item) error {
	completedVal := 0
	if item.Completed {
		completedVal = 1
	}
	_, err := s.db.Exec("INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)", item.ID, item.Name, completedVal)
	return err
}

func (s *sqliteDB) UpdateItem(id string, item Item) error {
	completedVal := 0
	if item.Completed {
		completedVal = 1
	}
	_, err := s.db.Exec("UPDATE todo_items SET name = ?, completed = ? WHERE id = ?", item.Name, completedVal, id)
	return err
}

func (s *sqliteDB) RemoveItem(id string) error {
	_, err := s.db.Exec("DELETE FROM todo_items WHERE id = ?", id)
	return err
}

func (s *sqliteDB) Close() error {
	return s.db.Close()
}

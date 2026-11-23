package persistence

import (
	"os"
)

// NewDB returns either MySQL or SQLite persistence implementation based on environment variables
func NewDB() (DB, error) {
	if os.Getenv("MYSQL_HOST") != "" || os.Getenv("MYSQL_HOST_FILE") != "" {
		return NewMySQLDB()
	}
	return NewSQLiteDB()
}

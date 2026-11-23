package persistence

// Item represents a todo item
type Item struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Completed bool   `json:"completed"`
}

// DB defines the data persistence interface for todo items
type DB interface {
	GetItems() ([]Item, error)
	GetItem(id string) (*Item, error)
	StoreItem(item Item) error
	UpdateItem(id string, item Item) error
	RemoveItem(id string) error
	Close() error
}

import sqlite3

def create_sample_database():
    # Creates a file called store.db in your project folder
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    # --- Create Tables ---

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            city TEXT,
            joined_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            stock INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # --- Insert Sample Data ---

    customers = [
        (1, "Amit Sharma",   "amit@email.com",   "Delhi",     "2024-01-15"),
        (2, "Priya Singh",   "priya@email.com",  "Mumbai",    "2024-02-20"),
        (3, "Rahul Verma",   "rahul@email.com",  "Bangalore", "2024-03-10"),
        (4, "Neha Gupta",    "neha@email.com",   "Chennai",   "2024-04-05"),
        (5, "Vikram Patel",  "vikram@email.com", "Pune",      "2024-05-18"),
    ]

    products = [
        (1, "Laptop",     "Electronics",  55000, 10),
        (2, "Phone",      "Electronics",  20000, 25),
        (3, "T-Shirt",    "Clothing",       799, 100),
        (4, "Jeans",      "Clothing",      1499, 60),
        (5, "Headphones", "Electronics",   2999, 40),
        (6, "Backpack",   "Accessories",   1299, 30),
    ]

    orders = [
        (1,  1, 2, 1, "2024-06-01"),
        (2,  2, 1, 1, "2024-06-03"),
        (3,  3, 3, 2, "2024-06-05"),
        (4,  4, 5, 1, "2024-06-07"),
        (5,  5, 6, 2, "2024-06-10"),
        (6,  1, 4, 1, "2024-06-12"),
        (7,  2, 5, 2, "2024-06-15"),
        (8,  3, 2, 1, "2024-06-18"),
        (9,  4, 3, 3, "2024-06-20"),
        (10, 5, 1, 1, "2024-06-22"),
    ]

    cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?)", customers)
    cursor.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", products)
    cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print("✅ Database created successfully! (store.db)")

if __name__ == "__main__":
    create_sample_database()
DROP TABLE IF EXISTS users;

CREATE TABLE users 
(
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

DROP TABLE IF EXISTS admin_logs;

CREATE TABLE admin_logs 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL, 
    photo_id INTEGER,
    title TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS admin_payment_logs;

CREATE TABLE admin_payment_logs
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    print_qty TEXT,
    total REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS photos;

CREATE TABLE photos 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    theme TEXT NOT NULL,
    file_path TEXT NOT NULL, 
    price_license REAL, 
    price_print REAL,
    inventory INTEGER DEFAULT 30
);

DROP TABLE IF EXISTS themes;

CREATE TABLE themes 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO themes (name) 
VALUES 
    ('Black & White'),
    ('Landscapes'),
    ('Seascapes'),
    ('Urban Life'),
    ('People & Portraits'),
    ('Adventure & Action')
;


DROP TABLE IF EXISTS limited_photos;

CREATE TABLE limited_photos 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT NOT NULL,
    base_price REAL NOT NULL, 
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,  
    end_date DATETIME NOT NULL 
);

SELECT * FROM limited_photos;


DROP TABLE IF EXISTS bids;

CREATE TABLE bids 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    bid_amount REAL NOT NULL,
    bid_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (photo_id) REFERENCES limited_photos(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


DROP TABLE IF EXISTS purchases;


CREATE TABLE purchases 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    photo_id INTEGER NOT NULL,
    license BOOLEAN DEFAULT 0,
    print_qty INTEGER DEFAULT 0,
    price_license REAL DEFAULT 0,
    price_print REAL DEFAULT 0,
    purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (photo_id) REFERENCES photos(id)
);


SELECT * FROM users;
UPDATE users SET is_admin = TRUE WHERE user_id = "db";

SELECT * FROM purchases;

DELETE FROM purchases;
DELETE FROM sqlite_sequence WHERE name='purchases';

SELECT * FROM limited_photos;
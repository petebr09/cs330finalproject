import sqlite3

connection = sqlite3.connect("animal_adoption.db")

cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS AdoptionApplication;")
cursor.execute("DROP TABLE IF EXISTS Animal;")
cursor.execute("DROP TABLE IF EXISTS Shelter;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Shelter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Animal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    breed TEXT,
    age INTEGER NOT NULL,
    description TEXT,
    image TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    matched BOOLEAN DEFAULT FALSE,
    shelter_id INTEGER NOT NULL,
    FOREIGN KEY (shelter_id) REFERENCES Shelter (id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS AdoptionApplication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    animal_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    message TEXT,
    FOREIGN KEY (animal_id) REFERENCES Animal (id)
);
""")

connection.commit()
connection.close()

print("Database and tables recreated successfully!")
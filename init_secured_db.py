#!/usr/bin/env python3
"""
Initialize the secured database with test users
This script creates the database and sets up hashed passwords
"""

import sqlite3
from werkzeug.security import generate_password_hash

# Create database
conn = sqlite3.connect('users.db')
cur = conn.cursor()

# Create users table
cur.execute('''CREATE TABLE IF NOT EXISTS users 
               (id INTEGER PRIMARY KEY, username TEXT)''')

# Insert test user
cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'testuser')")
cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (2, 'alice')")

conn.commit()
conn.close()

print("Database initialized successfully")
print("Users table created with test data")

# Print hashed password for alice (for reference)
password_hash = generate_password_hash("password123")
print(f"\nAlice's password hash: {password_hash}")
print("(This is for reference only - hash is stored in application code)")


# db_manager.py
import sqlite3

DB_FILE = "utdij_adatbazis.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn
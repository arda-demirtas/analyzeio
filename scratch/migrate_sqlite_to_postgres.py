import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# Configuration
SQLITE_DB = "/var/www/analyzeio/backend/analyzeio.db"
POSTGRES_DSN = "postgresql://analyzeio_user:p%40ssword_analyze_io_99@localhost/analyzeio"

def migrate():
    if not os.path.exists(SQLITE_DB):
        print(f"Error: SQLite database not found at {SQLITE_DB}")
        sys.exit(1)
        
    print(f"Connecting to SQLite: {SQLITE_DB}")
    lite_conn = sqlite3.connect(SQLITE_DB)
    lite_cur = lite_conn.cursor()
    
    print("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(POSTGRES_DSN)
    pg_cur = pg_conn.cursor()
    
    # 1. Migrate users
    print("Migrating table: users...")
    lite_cur.execute("SELECT id, username, email, hashed_password, is_premium, profile_picture, created_at FROM users")
    users = lite_cur.fetchall()
    
    # Convert is_premium from 0/1 to True/False
    processed_users = []
    for u in users:
        processed_users.append((
            u[0], u[1], u[2], u[3],
            bool(u[4]), u[5], u[6]
        ))
        
    pg_cur.execute("TRUNCATE TABLE users CASCADE")
    execute_values(pg_cur, 
        "INSERT INTO users (id, username, email, hashed_password, is_premium, profile_picture, created_at) VALUES %s", 
        processed_users
    )
    
    # 2. Migrate watchlists
    print("Migrating table: watchlists...")
    lite_cur.execute("SELECT id, user_id, symbol, created_at FROM watchlists")
    watchlists = lite_cur.fetchall()
    pg_cur.execute("TRUNCATE TABLE watchlists CASCADE")
    execute_values(pg_cur, 
        "INSERT INTO watchlists (id, user_id, symbol, created_at) VALUES %s", 
        watchlists
    )
    
    # 3. Migrate comments
    print("Migrating table: comments...")
    lite_cur.execute("SELECT id, symbol, user_id, content, created_at, parent_id FROM comments")
    comments = lite_cur.fetchall()
    pg_cur.execute("TRUNCATE TABLE comments CASCADE")
    execute_values(pg_cur, 
        "INSERT INTO comments (id, symbol, user_id, content, created_at, parent_id) VALUES %s", 
        comments
    )
    
    # 4. Migrate prediction_logs
    print("Migrating table: prediction_logs...")
    lite_cur.execute("SELECT id, symbol, interval, prediction_date, predicted_close, last_close, actual_close, created_at FROM prediction_logs")
    prediction_logs = lite_cur.fetchall()
    pg_cur.execute("TRUNCATE TABLE prediction_logs CASCADE")
    execute_values(pg_cur, 
        "INSERT INTO prediction_logs (id, symbol, interval, prediction_date, predicted_close, last_close, actual_close, created_at) VALUES %s", 
        prediction_logs
    )
    
    # 5. Migrate auto_train_symbols
    print("Migrating table: auto_train_symbols...")
    # Check if table exists in SQLite first
    lite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auto_train_symbols'")
    if lite_cur.fetchone():
        lite_cur.execute("SELECT id, symbol, created_at FROM auto_train_symbols")
        auto_train_symbols = lite_cur.fetchall()
        pg_cur.execute("TRUNCATE TABLE auto_train_symbols CASCADE")
        execute_values(pg_cur, 
            "INSERT INTO auto_train_symbols (id, symbol, created_at) VALUES %s", 
            auto_train_symbols
        )
    
    pg_conn.commit()
    print("All tables successfully migrated!")
    
    # 6. Reset sequences in PostgreSQL
    print("Resetting PostgreSQL primary key auto-increment sequences...")
    sequences = [
        ("users", "users_id_seq"),
        ("watchlists", "watchlists_id_seq"),
        ("comments", "comments_id_seq"),
        ("prediction_logs", "prediction_logs_id_seq"),
        ("auto_train_symbols", "auto_train_symbols_id_seq")
    ]
    
    for table, seq in sequences:
        pg_cur.execute(f"SELECT setval('{seq}', COALESCE((SELECT MAX(id)+1 FROM {table}), 1), false)")
        
    pg_conn.commit()
    print("All sequences reset successfully!")
    
    lite_conn.close()
    pg_conn.close()
    print("Migration finished!")

if __name__ == "__main__":
    migrate()

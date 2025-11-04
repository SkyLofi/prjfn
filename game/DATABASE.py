import sqlite3
import os

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Game saves table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_saves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Upgrades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cost INTEGER NOT NULL,
                increment INTEGER NOT NULL,
                description TEXT
            )
        ''')
        
        # User upgrades table (M:N relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_upgrades (
                user_id INTEGER,
                upgrade_id INTEGER,
                quantity INTEGER DEFAULT 1,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, upgrade_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (upgrade_id) REFERENCES upgrades (id) ON DELETE CASCADE
            )
        ''')
        
        # Insert default upgrades if not exists
        cursor.execute('SELECT COUNT(*) FROM upgrades')
        if cursor.fetchone()[0] == 0:
            default_upgrades = [
                ('Auto-Clicker', 10, 1, 'Generates 1 point per second'),
                ('Double Points', 50, 2, 'Each click gives 2 points'),
                ('Mega Clicker', 100, 5, 'Each click gives 5 points')
            ]
            cursor.executemany(
                'INSERT INTO upgrades (name, cost, increment, description) VALUES (?, ?, ?, ?)',
                default_upgrades
            )
        
        # Insert admin user if not exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                ('admin', 'admin', True)
            )
            cursor.execute(
                'INSERT INTO game_saves (user_id) VALUES (?)',
                (cursor.lastrowid,)
            )
        
        self.conn.commit()
    
    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()
    
    def create_user(self, username, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            cursor.execute(
                'INSERT INTO game_saves (user_id) VALUES (?)',
                (cursor.lastrowid,)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user_save(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM game_saves WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def update_user_save(self, user_id, score, clicks):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE game_saves SET score = ?, clicks = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?',
            (score, clicks, user_id)
        )
        self.conn.commit()
    
    def get_all_upgrades(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM upgrades')
        return cursor.fetchall()
    
    def get_user_upgrades(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.*, uu.quantity 
            FROM upgrades u 
            JOIN user_upgrades uu ON u.id = uu.upgrade_id 
            WHERE uu.user_id = ?
        ''', (user_id,))
        return cursor.fetchall()
    
    def add_user_upgrade(self, user_id, upgrade_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO user_upgrades (user_id, upgrade_id) VALUES (?, ?)',
                (user_id, upgrade_id)
            )
        except sqlite3.IntegrityError:
            cursor.execute(
                'UPDATE user_upgrades SET quantity = quantity + 1 WHERE user_id = ? AND upgrade_id = ?',
                (user_id, upgrade_id)
            )
        self.conn.commit()
    
    def get_leaderboard(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.username, gs.score, gs.clicks 
            FROM game_saves gs 
            JOIN users u ON gs.user_id = u.id 
            ORDER BY gs.score DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, username, is_admin, created_at FROM users')
        return cursor.fetchall()
    
    def delete_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import logging



# Set up log rotation: 1MB per file, keep 5 backups
from logging.handlers import RotatingFileHandler
log_handler = RotatingFileHandler('app.log', maxBytes=1_000_000, backupCount=5)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, logging.StreamHandler()]
)

app = Flask(__name__)
# Secret key for Flask session management
app.secret_key = 'bomboclaat'
# Secret admin key for score editing (used in /edit_scores route)
ADMIN_EDIT_KEY = 'editallbomboclaat'
@app.route('/edit_scores', methods=['GET', 'POST'])
def edit_scores():
    """
    Admin route to edit any user's score. Requires ADMIN_EDIT_KEY.
    GET: Show all users and scores for editing.
    POST: Update a user's score if the correct admin key is provided.
    """
    if request.method == 'POST':
        key = request.form.get('admin_key')
        new_score = request.form.get('new_score')
        user_id = request.form.get('user_id')
        if key == ADMIN_EDIT_KEY:
            try:
                conn = get_db_connection()
                conn.execute('UPDATE game_saves SET score = ? WHERE user_id = ?', (new_score, user_id))
                conn.commit()
                conn.close()
                flash(f'Score for user {user_id} updated to {new_score}.', 'success')
                logging.info(f'Admin updated score for user {user_id} to {new_score}')
            except Exception as e:
                flash(f'Error updating score: {e}', 'error')
                logging.error(f'Error updating score for user {user_id}: {e}')
        else:
            flash('Invalid admin key.', 'error')
            logging.warning(f'Invalid admin key attempt for score edit (user_id={user_id})')
        return redirect(url_for('edit_scores'))
    # Show all users and scores for editing
    conn = get_db_connection()
    users = conn.execute('SELECT u.id, u.username, gs.score FROM users u JOIN game_saves gs ON u.id = gs.user_id').fetchall()
    conn.close()
    return render_template('edit_scores.html', users=users)
DATABASE = 'DATABASE.db'

def get_db_connection():
    """
    Create and return a new SQLite database connection.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """
    Main page: Shows leaderboard and user info if logged in.
    """
    conn = get_db_connection()
    leaderboard = conn.execute('''
        SELECT u.username, gs.score 
        FROM game_saves gs 
        JOIN users u ON gs.user_id = u.id 
        ORDER BY gs.score DESC 
        LIMIT 10
    ''').fetchall()
    conn.close()
    
    user = None
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, username, is_admin FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()
        conn.close()
    
    # Get user's score if logged in
    user_score = None
    if user:
        conn = get_db_connection()
        score_row = conn.execute('SELECT score FROM game_saves WHERE user_id = ?', (user['id'],)).fetchone()
        if score_row:
            user_score = score_row['score']
        conn.close()
    # Clear the score increment flash flag so the button can be clicked again
    if session.get('score_incremented_flash'):
        session.pop('score_incremented_flash')
    return render_template('index.html', leaderboard=leaderboard, user=user, user_score=user_score)
@app.route('/increment_score', methods=['POST'])
def increment_score():
    """
    Increments the logged-in user's score by 1. Prevents duplicate flash messages.
    """
    if 'user_id' not in session:
        flash('You must be logged in to increment your score.', 'error')
        logging.warning('Score increment attempt without login')
        return redirect(url_for('index'))
    # Prevent duplicate flash message
    if session.get('score_incremented_flash'):
        session.pop('score_incremented_flash')
        return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('UPDATE game_saves SET score = score + 1 WHERE user_id = ?', (session['user_id'],))
    conn.commit()
    conn.close()
    flash('Score incremented!', 'success')
    session['score_incremented_flash'] = True
    logging.info(f'User {session["user_id"]} incremented their score')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route: Authenticates user and starts session.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash('Login successful!', 'success')
            logging.info(f'User {username} logged in (id={user["id"]})')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
            logging.warning(f'Failed login attempt for username: {username}')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration route: Creates a new user and initializes their game save.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.execute(
                'INSERT INTO game_saves (user_id) VALUES (?)',
                (user_id,)
            )
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            logging.info(f'New user registered: {username} (id={user_id})')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already exists', 'error')
            logging.warning(f'Registration failed: username already exists ({username})')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """
    Logout route: Clears session and redirects to index.
    """
    session.clear()
    flash('You have been logged out', 'info')
    logging.info('User logged out')
    return redirect(url_for('index'))

@app.route('/leaderboard')
def leaderboard():
    """
    Shows the full leaderboard with scores and clicks.
    """
    conn = get_db_connection()
    leaderboard = conn.execute('''
        SELECT u.username, gs.score, gs.clicks 
        FROM game_saves gs 
        JOIN users u ON gs.user_id = u.id 
        ORDER BY gs.score DESC
    ''').fetchall()
    conn.close()
    
    user = None
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, username, is_admin FROM users WHERE id = ?',
            (session['user_id'],)
        ).fetchone()
        conn.close()
    
    return render_template('leaderboard.html', leaderboard=leaderboard, user=user)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """
    Admin panel: Allows admin users to delete users.
    """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        logging.warning('Unauthorized admin panel access attempt')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        if 'delete_user' in request.form:
            user_id = request.form['user_id']
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            flash('User deleted successfully', 'success')
            logging.info(f'Admin deleted user {user_id}')
    
    users = conn.execute('SELECT id, username, is_admin, created_at FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
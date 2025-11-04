# Flask Game Leaderboard & Admin Panel

This project is a simple Flask web application for user registration, login, and a game leaderboard. Users can increment their score, and admins can edit any user's score or delete users.

## Features
- User registration and login
- Session management
- Leaderboard display
- Increment score button for logged-in users
- Admin panel for user management
- Secret admin key for editing any user's score

## Setup
1. **Install dependencies:**
   ```bash
   pip install flask
   ```
2. **Initialize the database:**
   ```bash
   python web/init_db.py
   ```
3. **Run the app:**
   ```bash
   python web/app.py
   ```

## Usage
- Visit `http://127.0.0.1:5000` in your browser.
- Register a new user and log in.
- Click the "Add 1 to Score" button to increment your score.
- Access `/edit_scores` to edit any user's score (requires admin key).
- Access `/admin` for user management (admin only).

## Security Notes
- The secret key and admin key are hardcoded for demo purposes. Use environment variables in production.
- Passwords are stored in plaintext. Use password hashing for real applications.

## File Structure
- `web/app.py` - Main Flask application
- `web/init_db.py` - Database initialization script
- `web/templates/` - HTML templates
- `game/` - Game logic (not included in this demo)

## License
MIT

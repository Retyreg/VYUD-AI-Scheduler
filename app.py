import logging
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

# Configure logging
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# Database setup
DATABASE = 'posts.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS post_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        content TEXT,
        status TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------------------------
# Legacy endpoints (keep for backward compatibility)
# ---------------------------------------------------------------------------

@app.route('/post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        platform = data.get('platform')
        content = data.get('content')
        status = data.get('status')
        timestamp = data.get('timestamp') or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO post_history (platform, content, status, timestamp) VALUES (?, ?, ?, ?)',
                  (platform, content, status, timestamp))
        conn.commit()
        post_id = c.lastrowid
        conn.close()
        logging.info(f'Post created: {content}')
        return jsonify({'message': 'Post created successfully', 'id': post_id}), 201
    except Exception as e:
        logging.error(f'Error creating post: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/post/history', methods=['GET'])
def get_post_history():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM post_history')
        posts = c.fetchall()
        conn.close()
        logging.info('Fetched post history')
        return jsonify(posts), 200
    except Exception as e:
        logging.error(f'Error fetching post history: {e}')
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------------------------------------
# /api/posts/ — canonical REST endpoints used by publisher.vyud.tech
# ---------------------------------------------------------------------------

def _row_to_dict(row):
    """Convert a DB row tuple to a dict."""
    return {
        'id': row[0],
        'platform': row[1],
        'content': row[2],
        'status': row[3],
        'timestamp': row[4],
    }

@app.route('/api/posts/', methods=['GET'])
def api_list_posts():
    """
    List posts with optional filtering.

    Query params:
      status   — filter by status value (e.g. "scheduled", "success", "error")
      platform — filter by platform name (e.g. "Telegram", "LinkedIn")
    """
    try:
        status_filter = request.args.get('status')
        platform_filter = request.args.get('platform')

        query = 'SELECT * FROM post_history WHERE 1=1'
        params = []

        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)
        if platform_filter:
            query += ' AND platform = ?'
            params.append(platform_filter)

        query += ' ORDER BY timestamp DESC'

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(query, params)
        posts = [_row_to_dict(row) for row in c.fetchall()]
        conn.close()

        logging.info('GET /api/posts/ returned %d records', len(posts))
        return jsonify(posts), 200
    except Exception as e:
        logging.error(f'Error listing posts: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/', methods=['POST'])
def api_create_post():
    """Create a new post record (used by publisher.vyud.tech and auto_post.py)."""
    try:
        data = request.get_json()
        platform = data.get('platform')
        content = data.get('content')
        status = data.get('status', 'scheduled')
        timestamp = data.get('timestamp') or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO post_history (platform, content, status, timestamp) VALUES (?, ?, ?, ?)',
                  (platform, content, status, timestamp))
        conn.commit()
        post_id = c.lastrowid
        conn.close()

        logging.info('POST /api/posts/ id=%d platform=%s status=%s', post_id, platform, status)
        return jsonify(_row_to_dict((post_id, platform, content, status, timestamp))), 201
    except Exception as e:
        logging.error(f'Error creating post via /api/posts/: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['PATCH'])
def api_update_post(post_id):
    """
    Update post fields (status, timestamp, content).
    Used by the scheduler when a scheduled post is published.
    """
    try:
        data = request.get_json()

        allowed = {'platform', 'content', 'status', 'timestamp'}
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Keys are validated against a fixed allowlist above, so the f-string
        # interpolation here only ever inserts known column names (no SQL injection risk).
        # All user-supplied values are passed as parameterised query arguments (?).
        set_clause = ', '.join(f'{k} = ?' for k in updates)
        values = list(updates.values()) + [post_id]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(f'UPDATE post_history SET {set_clause} WHERE id = ?', values)
        if c.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        conn.commit()
        c.execute('SELECT * FROM post_history WHERE id = ?', (post_id,))
        row = c.fetchone()
        conn.close()

        logging.info('PATCH /api/posts/%d fields=%s', post_id, list(updates.keys()))
        return jsonify(_row_to_dict(row)), 200
    except Exception as e:
        logging.error(f'Error updating post {post_id}: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    """Delete a post record."""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('DELETE FROM post_history WHERE id = ?', (post_id,))
        if c.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        conn.commit()
        conn.close()

        logging.info('DELETE /api/posts/%d', post_id)
        return jsonify({'message': f'Post {post_id} deleted'}), 200
    except Exception as e:
        logging.error(f'Error deleting post {post_id}: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

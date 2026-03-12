import logging
import os
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

# Configure logging
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# ---------------------------------------------------------------------------
# Database abstraction — SQLite (default) or PostgreSQL via DATABASE_URL
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")   # e.g. postgresql://user:pass@host/db
SQLITE_FILE = os.environ.get("SQLITE_FILE", "posts.db")

_USE_POSTGRES = bool(DATABASE_URL)

if _USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
        logging.info("Database backend: PostgreSQL (%s)", DATABASE_URL.split("@")[-1])
    except ImportError:
        logging.error(
            "DATABASE_URL is set but psycopg2 is not installed. "
            "Run: pip install psycopg2-binary"
        )
        raise
else:
    logging.info("Database backend: SQLite (%s)", SQLITE_FILE)

# SQL placeholder differs between drivers
_PH = "%s" if _USE_POSTGRES else "?"


def _get_conn():
    """Return a live database connection (PostgreSQL or SQLite)."""
    if _USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(SQLITE_FILE)


def _fetchall(cursor):
    """Fetch all rows as plain tuples regardless of backend."""
    return cursor.fetchall()


def init_db():
    """Create the post_history table if it does not already exist."""
    conn = _get_conn()
    c = conn.cursor()
    if _USE_POSTGRES:
        c.execute("""
            CREATE TABLE IF NOT EXISTS post_history (
                id        SERIAL PRIMARY KEY,
                platform  TEXT,
                content   TEXT,
                status    TEXT,
                timestamp TEXT
            )
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS post_history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                platform  TEXT,
                content   TEXT,
                status    TEXT,
                timestamp TEXT
            )
        """)
    conn.commit()
    conn.close()


init_db()


def _row_to_dict(row):
    """Convert a DB row tuple to a dict."""
    return {
        'id': row[0],
        'platform': row[1],
        'content': row[2],
        'status': row[3],
        'timestamp': row[4],
    }


def _insert_post(platform, content, status, timestamp):
    """Insert a post and return its new ID."""
    conn = _get_conn()
    c = conn.cursor()
    if _USE_POSTGRES:
        c.execute(
            f"INSERT INTO post_history (platform, content, status, timestamp) "
            f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}) RETURNING id",
            (platform, content, status, timestamp),
        )
        post_id = c.fetchone()[0]
    else:
        c.execute(
            f"INSERT INTO post_history (platform, content, status, timestamp) "
            f"VALUES ({_PH}, {_PH}, {_PH}, {_PH})",
            (platform, content, status, timestamp),
        )
        post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id

# ---------------------------------------------------------------------------
# Legacy endpoints (kept for backward compatibility)
# ---------------------------------------------------------------------------

@app.route('/post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        platform = data.get('platform')
        content = data.get('content')
        status = data.get('status')
        timestamp = data.get('timestamp') or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        post_id = _insert_post(platform, content, status, timestamp)
        logging.info('Post created: %s', content[:80])
        return jsonify({'message': 'Post created successfully', 'id': post_id}), 201
    except Exception as e:
        logging.error('Error creating post: %s', e)
        return jsonify({'error': str(e)}), 500


@app.route('/post/history', methods=['GET'])
def get_post_history():
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM post_history')
        posts = _fetchall(c)
        conn.close()
        logging.info('Fetched post history')
        return jsonify(posts), 200
    except Exception as e:
        logging.error('Error fetching post history: %s', e)
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------------------------------------
# /api/posts/ — canonical REST endpoints used by publisher.vyud.tech
# ---------------------------------------------------------------------------

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
            query += f' AND status = {_PH}'
            params.append(status_filter)
        if platform_filter:
            query += f' AND platform = {_PH}'
            params.append(platform_filter)

        query += ' ORDER BY timestamp DESC'

        conn = _get_conn()
        c = conn.cursor()
        c.execute(query, params)
        posts = [_row_to_dict(row) for row in _fetchall(c)]
        conn.close()

        logging.info('GET /api/posts/ returned %d records', len(posts))
        return jsonify(posts), 200
    except Exception as e:
        logging.error('Error listing posts: %s', e)
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

        post_id = _insert_post(platform, content, status, timestamp)

        logging.info('POST /api/posts/ id=%d platform=%s status=%s', post_id, platform, status)
        return jsonify(_row_to_dict((post_id, platform, content, status, timestamp))), 201
    except Exception as e:
        logging.error('Error creating post via /api/posts/: %s', e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/posts/<int:post_id>', methods=['PATCH'])
def api_update_post(post_id):
    """
    Update post fields (status, timestamp, content).
    Used by the scheduler when a scheduled post is published.
    Typical transition: scheduled → success | error
    """
    try:
        data = request.get_json()

        # Explicit mapping of allowed field names to their SQL column names.
        # Only these four columns may be updated; any other keys in the request
        # body are silently ignored.  Values are always passed as parameterised
        # query arguments — never interpolated into the SQL string.
        ALLOWED_COLUMNS = {
            'platform': 'platform',
            'content': 'content',
            'status': 'status',
            'timestamp': 'timestamp',
        }
        updates = {ALLOWED_COLUMNS[k]: v for k, v in data.items() if k in ALLOWED_COLUMNS}
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Column names come exclusively from ALLOWED_COLUMNS keys — safe to
        # interpolate.  All user-supplied values are parameterised (?/%s).
        set_clause = ', '.join(f'{col} = {_PH}' for col in updates)
        values = list(updates.values()) + [post_id]

        conn = _get_conn()
        c = conn.cursor()
        c.execute(f'UPDATE post_history SET {set_clause} WHERE id = {_PH}', values)
        if c.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        conn.commit()
        c.execute(f'SELECT * FROM post_history WHERE id = {_PH}', (post_id,))
        row = c.fetchone()
        conn.close()

        logging.info('PATCH /api/posts/%d fields=%s', post_id, list(updates.keys()))
        return jsonify(_row_to_dict(row)), 200
    except Exception as e:
        logging.error('Error updating post %d: %s', post_id, e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    """Delete a post record."""
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(f'DELETE FROM post_history WHERE id = {_PH}', (post_id,))
        if c.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Post not found'}), 404
        conn.commit()
        conn.close()

        logging.info('DELETE /api/posts/%d', post_id)
        return jsonify({'message': f'Post {post_id} deleted'}), 200
    except Exception as e:
        logging.error('Error deleting post %d: %s', post_id, e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

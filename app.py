import logging
import sqlite3
from flask import Flask, request, jsonify

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

@app.route('/post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        platform = data.get('platform')
        content = data.get('content')
        status = data.get('status')
        timestamp = data.get('timestamp')

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO post_history (platform, content, status, timestamp) VALUES (?, ?, ?, ?)',
                  (platform, content, status, timestamp))
        conn.commit()
        conn.close()
        logging.info(f'Post created: {content}')
        return jsonify({'message': 'Post created successfully'}), 201
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

if __name__ == '__main__':
    app.run(debug=True)

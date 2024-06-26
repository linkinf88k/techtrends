import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Global variable to track the connection count
global_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global global_connection_count

    # Increase the connection count each time the function is called
    global_connection_count += 1

    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error(f'Article with id {post_id} does not exist!')
      return render_template('404.html'), 404
    else:
        title = post['title']
        app.logger.info(f"Article {title} retrieved!")
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("The About Us page is rendered")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            app.logger.info(f"Article {title} created!")
            return redirect(url_for('index'))

    return render_template('create.html')

# Define Healthcheck endpoint
@app.route('/healthz')
def abhealthzout():
    data = { "result": "OK - healthy"}
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Health check request successful')
    return response

# Define Metrics endpoint
@app.route('/metrics')
def metrics():
    try:
        conn = get_db_connection()

        # Count the total number of posts in the database
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM posts')
        post_count = cursor.fetchone()[0]
        conn.close()

        metrics = {
            "db_connection_count": global_connection_count,
            "post_count": post_count
        }

        return jsonify(metrics), 200

    except Exception as e:
        return jsonify(result="ERROR - " + str(e)), 500

# start the application on port 3111
if __name__ == "__main__":
   logging.basicConfig(level=logging.DEBUG, handlers=[logging.FileHandler("app.log"), logging.StreamHandler(sys.stdout)])
   app.run(host='0.0.0.0', port='3111')

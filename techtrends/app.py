import sqlite3
import logging, sys
from subprocess import Popen, PIPE

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

FORMAT = '%(levelname)s:%(name)s: %(asctime)-15s %(message)s'

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
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

def get_post_count():
    connection = get_db_connection()
    count = connection.execute('SELECT COUNT() FROM posts').fetchone()[0]
    connection.close()
    return count

def get_conn_count():
    # based on: https://stackoverflow.com/a/23647374
    proc = Popen(['lsof', 'database.db'], stdout=PIPE)
    count = sum(1 for _ in proc.stdout)
    if count > 0:
        count-=1
    return count

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
      app.logger.info('Article (id: %d) not found.', post_id)
      return render_template('404.html'), 404
    else:
      app.logger.info('Article %s retrieved!', post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About page accessed')
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

            app.logger.info('Article %s created!', title)
            return redirect(url_for('index'))

    return render_template('create.html')

# Healthcheck Endpoint
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    return response

@app.route('/metrics')
def metrics():
    post_count = get_post_count()
    db_connection_count = get_conn_count()
    response = app.response_class(
            response=json.dumps({"db_connection_count":db_connection_count, "post_count":post_count}),
            status=200,
            mimetype='application/json'
    )

    return response

# start the application on port 3111
if __name__ == "__main__":

    ## log to a file
    sout = logging.StreamHandler(sys.stdout)
    serr = logging.StreamHandler(sys.stderr)
    logging.basicConfig(format=FORMAT, level=logging.DEBUG, handlers=[sout,serr])
    
    app.run(host='0.0.0.0', port='3111')

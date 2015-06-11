import flask
from haploqa import app

@app.route('/index.html')
@app.route('/')
def index():
    return flask.render_template('index.html')

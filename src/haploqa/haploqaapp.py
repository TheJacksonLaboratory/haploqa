import flask
#import haploqa.haploqa

app = flask.Flask(__name__)

@app.route('/index.html')
@app.route('/')
def index():
    return flask.render_template('index.html')

# @app.route('/dataimport.html')
# def dataimport_view():
#     return flask.render_template('dataimport.html')

if __name__ == '__main__':
    app.debug = True
    app.run()

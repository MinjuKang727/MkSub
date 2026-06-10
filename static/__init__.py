from flask import Flask

app = Flask(__name__)  # Flask 앱 생성

@app.route('/')
def index():
    return 'welcome'

@app.route('/create/')
def create():
    return 'Create'

@app.route('/read/<id>/')
def read(id):
    print(id)
    return 'Read' + id

app.run(debug=True)

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    print('Starting simple Flask app...')
    print('Running on http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=True)

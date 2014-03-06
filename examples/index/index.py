from flask import Flask
from flask import render_template
app = Flask(__name__)
app.debug = True
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5Mb

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
from flask import Flask,redirect, url_for

app = Flask (__name__)
a=False

@app.route('/home')
def home():
    return "Hello, This is a simple Flask app!" "<h1>HEY</h1>"

@app.route('/name/<name>')
def user(name):
    return f"Hello, {name}!"

@app.route('/admin')
def admin():
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/day')
def dayData():
    pass

@app.route('/data/month')
def monthData():
    pass

@app.route('/data/year')
def yearData():
    pass

app.run()
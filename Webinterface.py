from flask import Flask, render_template, request, abort, make_response, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Data API
@app.route('/api/json/data')
def data():
    return 'data'

@app.route('/api/json/data/day')
def day_data():
    return 'day data'

@app.route('/api/json/data/week')
def week_data():
    return 'week data'

@app.route('/api/json/data/month')
def month_data():
    return 'month data'

@app.route('/api/json/data/year')
def year_data():
    return 'year data'

@app.route('/api/json/data/years')
def years_data():
    return 'years data'

# Electric meter API
@app.route('/api/json/electric-meter')
def electric_meter():
    return 'electric meter'

@app.route('/api/json/electric-meter/add')
def add_electric_meter():
    return 'add electric meter'

@app.route('/api/json/electric-meter/remove')
def remove_electric_meter():
    return 'remove electric meter'

@app.route('/api/json/electric-meter/change')
def change_electric_meter():
    return 'change electric meter'

# Database API
@app.route('/api/json/database')
def database():
    return 'database'

@app.route('/api/json/database/add')
def add_database():
    return 'add database'

@app.route('/api/json/database/remove')
def remove_database():
    return 'remove database'

#app.run()
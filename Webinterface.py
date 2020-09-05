from flask import Flask, render_template, request, abort, make_response, jsonify

app = Flask(__name__)

# TODO dokumentieren und verwenden
api_codes = {"missing_parameter": 100,
             "invalid_type": 200,
             "invalid_values": 300
             }

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
    # TODO write test for parse_parameter_json
    params = parse_parameter_json((('value', float), ('pin', int), ('active-low', bool), ('name', str)))

    invalid_parameter_value = []
    # Check parameter value
    # TODO objekt das in liste eingefügt wird vielleicht über funktion auslagern
    # TODO vllt auch noch api status code einfügen
    if params['value'] <= 0:
        invalid_parameter_value.append({"parameter": "value",
                                        "message": "must be greater than 0"
                                        })
    if params['pin'] <= 0:
        invalid_parameter_value.append({"parameter": "pin",
                                        "message": "must be greater than 0"
                                        })
    # TODO Namenslänge ohne whitespace character > 0
    if not bool(params['name']):
        invalid_parameter_value.append({"parameter": "name",
                                        "message": "must contain text"
                                        })

    if len(invalid_parameter_value) > 0:
        abort_parameter('invalid parameter value', invalid_parameter_value)



    return ''

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


# Helper functions
# TODO test
def parse_parameter_json(expected_parameter, arguments=None):
    if arguments is None:
        arguments = request.args

    # Check if parameter is of type 'param_type'
    def is_param_of_type(param_name, param_type):
        param = arguments[param_name]
        # Test bool
        if param_type is bool:
            return param in ('True', 'true', 'False', 'false')
        else:
            # Test other types by trying to cast param
            try:
                param_type(param)
                return True
            except ValueError:
                return False

    # Parse param into specified param_type
    def parse_param(param_name, param_type):
        param = arguments[param_name]
        # Special case for parsing bool
        if param_type is bool:
            return param in ('True', 'true')
        return param_type(param)

    # Create list of parameters missing in arguments
    missing_parameters = [param for param, param_type in expected_parameter if param not in arguments.keys()]
    # return json error
    if len(missing_parameters) > 0:
        abort_parameter('missing parameters', missing_parameters)
        """json_message = jsonify({
            "code": 400,
            "info": "missing parameters",
            "parameters": missing_parameters
        })
        response = make_response(json_message, 400)
        abort(response)"""

    # Create list of parameters having the wrong type
    invalid_types = [{"parameter": param, "expected_type": str(param_type)}
                     for param, param_type in expected_parameter
                     if not is_param_of_type(param, param_type)]

    if len(invalid_types) > 0:
        abort_parameter('invalid parameter type', invalid_types)

    dic = {param_name: parse_param(param_name, param_type) for param_name, param_type in expected_parameter}
    return dic


def abort_parameter(info, parameter_list):
    json_message = jsonify({
        "code": 400,
        "info": info,
        "parameters": parameter_list
    })
    response = make_response(json_message, 400)
    abort(response)

if app.config['ENV'] == 'development':
    app.run()

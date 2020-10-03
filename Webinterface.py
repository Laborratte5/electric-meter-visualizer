from flask import Flask, render_template, request, abort, make_response, jsonify

from Logic import Logic

app = Flask(__name__)
development_mode = app.config['ENV'] == 'development'

logic = Logic(development_mode)

# TODO dokumentieren und verwenden
api_codes = {"missing_parameter": 100,
             "invalid_type": 200,
             "invalid_value": 300,
             "no_electric_meter_id": 400
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
    #return 'day data'
    data = logic.get_day()
    return str(logic.get_day())

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
# TODO test
@app.route('/api/json/electric-meter')
def electric_meter():
    # Supplied id means return only electric meter with this id
    if 'id' in request.args.keys():
        params = parse_parameter_json(('id', int))
        id = params['id']
        # Search for electric meter witch specific id
        try:
            electric_meter = logic.get_electric_meter(id)
            electric_meters_json = electric_meter_to_dic(electric_meter)
            return {
                "electric-meter": electric_meters_json
            }
        except KeyError:
            abort_no_electric_meter_with_id(id)
    # No id means return all electric meter
    else:
        electric_meters = logic.get_electric_meters()
        electric_meters_json = [{"id": id, "electric_meter": electric_meter_to_dic(electric_meter)}
                                for id, electric_meter in electric_meters]
        return {
            "electric-meters": electric_meters_json
        }

@app.route('/api/json/electric-meter/add')
def add_electric_meter():
    # TODO write test for parse_parameter_json
    params = parse_parameter_json(('value', float), ('pin', int), ('active-low', bool), ('name', str))

    invalid_parameter_value = []
    # Check parameter value
    # TODO objekt das in liste 'invalid_parameter_value' eingefügt wird vielleicht über funktion auslagern
    # TODO vllt auch noch api status code einfügen
    value = params['value']
    pin = params['pin']
    active_low = params['active-low']
    name = params['name']

    if value <= 0:
        invalid_parameter_value.append({"parameter": "value",
                                        "message": "must be greater than 0"
                                        })
    if pin <= 0:
        invalid_parameter_value.append({"parameter": "pin",
                                        "message": "must be greater than 0"
                                        })
    # TODO Namenslänge ohne whitespace character > 0
    if not bool(name):
        invalid_parameter_value.append({"parameter": "name",
                                        "message": "must contain text"
                                        })

    if len(invalid_parameter_value) > 0:
        abort_parameter('invalid parameter value', invalid_parameter_value)

    # Add new electric meter
    new_meter, id = logic.add_electric_meter(value, pin, active_low=active_low, name=name)
    json_response = {
                    "id": id,
                    "new_meter": electric_meter_to_dic(new_meter)
                    }
    return json_response

@app.route('/api/json/electric-meter/remove')
def remove_electric_meter():
    # Parse parameter
    params = parse_parameter_json(('id', int))
    id = params['id']
    # Remove electric meter with id and return it
    try:
        removed_meter = logic.remove_electric_meter(id)
        return electric_meter_to_dic(removed_meter)
    #
    except KeyError as e:
        abort_no_electric_meter_with_id(id)

@app.route('/api/json/electric-meter/change')
def change_electric_meter():
    params = parse_parameter_json(('id', int))

    id = params['id']
    value = None
    pin = None
    active_low = None
    name = None

    # TODO check parameter values
    if 'value' in request.args.keys():
        params = parse_parameter_json(('value', float))
        value = params['value']
    if 'pin' in request.args.keys():
        params = parse_parameter_json(('pin', int))
        pin = params['pin']
    if 'active-low' in request.args.keys():
        params = parse_parameter_json(('active-low', bool))
        active_low = params['active-low']
    if 'name' in request.args.keys():
        params = parse_parameter_json(('name', str))
        name = params['name']

    try:
        changed_meter = logic.change_electric_meter(id, value, pin, active_low, name)
        return electric_meter_to_dic(changed_meter)
    except KeyError as e:
        abort_no_electric_meter_with_id(id)


# Helper functions
# TODO test
def parse_parameter_json(*expected_parameter, arguments=None):
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


def abort_no_electric_meter_with_id(id):
    json_message = jsonify({
        "code": 400,
        "info": "no electric meter with this id found",
        "id": int(id)
    })
    response = make_response(json_message, 400)
    abort(response)


def electric_meter_to_dic(electric_meter):
    return {
        "name": electric_meter.name,
        "value": electric_meter.value,
        "pin": electric_meter.pin,
        "active-low": electric_meter.active_low
    }


if development_mode:
    app.run()

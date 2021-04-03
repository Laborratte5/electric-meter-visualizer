from deprecated import deprecated

from flask import Flask, render_template, request, abort, make_response, jsonify
from marshmallow import Schema, fields, ValidationError, validate

from ConfigLoader import Config
from Logic import Logic

app = Flask(__name__)
development_mode = app.config['ENV'] == 'development'

logic = Logic(Config.get_config(), development_mode)


@app.route('/')
def index():
    return render_template('index.html')


# Data API
@app.route('/api/json/data')
def data():
    return 'data'


@app.route('/api/json/data/raw')
def raw_data():
    data = logic.get_raw()
    return dict(data)


@app.route('/api/json/data/day')
def day_data():
    # TODO convert dict to dict better suitable for chart.js
    if 't' in request.args.keys():
        t_minus = int(request.args['t'])
        data = logic.get_day(t_minus)
    else:
        data = logic.get_day()
    return dict(data)


@app.route('/api/json/data/week')
def week_data():
    return 'week data'


@app.route('/api/json/data/month')
def month_data():
    if 't' in request.args.keys():
        t_minus = int(request.args['t'])
        data = logic.get_month(t_minus)
    else:
        data = logic.get_month()
    return dict(data)


@app.route('/api/json/data/year')
def year_data():
    if 't' in request.args.keys():
        t_minus = int(request.args['t'])
        data = logic.get_year(t_minus)
    else:
        data = logic.get_year()
    return dict(data)


@app.route('/api/json/data/years')
def years_data():
    data = logic.get_years()
    return dict(data)


# Electric meter API
@app.route('/electric-meter', methods=['GET'])
def get_electric_meter():
    # TODO marshmallow
    # Utility method to create a json response
    def create_json_response(electric_meters):
        return {
            "total_number": len(electric_meters),
            "electric_meters": [electric_meter_to_dic(meter_id, electric_meter)
                                for meter_id, electric_meter in electric_meters]
        }
    # Supplied id means return only electric meter with this id
    if 'id' in request.args.keys():
        # Search for electric meter witch specific id
        try:
            id = int(request.args['id'])
            electric_meter = [(id, logic.get_electric_meter(id))]  # Wrap meter in list of (id, meter) tupel
            return create_json_response(electric_meter)
        except KeyError:
            abort_meter_not_found('no electric meter with requested id exist')
        except ValueError:
            abort_meter_not_found('electric meter id must be a integer')
    # No id means return all electric meter
    else:
        electric_meters = logic.get_electric_meters()
        return create_json_response(electric_meters)


@app.route('/electric-meter', methods=['POST'])
def add_electric_meter():
    # Parse request
    meter_dict = AddElectricMeterSchema().load(request.get_json())

    # Add new electric meter
    new_meter, id = logic.add_electric_meter(**meter_dict)

    json_response = {
        "id": id,
        "new_meter": electric_meter_to_dic(id, new_meter)
    }

    return json_response, 201


@app.route('/electric-meter', methods=['DELETE'])
def delete_electric_meter():
    abort(501)
    # TODO
"""
    # Parse parameter
    params = parse_parameter_json(('id', int))
    id = params['id']
    # Remove electric meter with id and return it
    try:
        removed_meter = logic.remove_electric_meter(id)
        return electric_meter_to_dic(removed_meter)
    #
    except KeyError as e:
        abort_meter_not_found('no electric meter with requested id exist')
"""

@app.route('/electric-meter', methods=['PATCH'])
def change_electric_meter():
    abort(501)
"""
    # TODO
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
        pass
        #abort_no_electric_meter_with_id(id)
"""


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    response = {
        'code': "INVALID_PARAMETER",
        'parameter': list(error.messages.keys()),
        'info': error.messages
    }

    return response, 400

# Helper functions
# TODO remove parse_parameter_json_function
"""
def parse_parameter_json(*expected_parameter):
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

    # Create list of parameters having the wrong type
    invalid_types = [{"parameter": param, "expected_type": str(param_type)}
                     for param, param_type in expected_parameter
                     if not is_param_of_type(param, param_type)]

    if len(invalid_types) > 0:
        abort_parameter('invalid parameter type', invalid_types)

    dic = {param_name: parse_param(param_name, param_type) for param_name, param_type in expected_parameter}
    return dic
"""


def abort_parameter(info, parameter_list):
    json_message = jsonify({
        "code": 400,
        "info": info,
        "parameters": parameter_list
    })
    response = make_response(json_message, 400)
    abort(response)


def abort_meter_not_found(info):
    response = make_response(make_error_response('ELECTRIC_METER_NOT_FOUND', info), 404)
    abort(response)


@deprecated()
def make_error_response(api_error_code, message, info=None, error_code=400):
    if info is None:
        info = {}

    return {
        'code': error_code,
        'message': message,
        'info': info
    }



@deprecated("Use marshmallow to convert electric meters to dict/json")
def electric_meter_to_dic(meter_id, electric_meter):
    return {
        'id': meter_id,
        'name': electric_meter.name,
        'pin': electric_meter.pin,
        'active_low': electric_meter.active_low,
        'value': electric_meter.value,
        'current_value': electric_meter.get_amount()
    }


#if development_mode:
#    app.run()

class AddElectricMeterSchema(Schema):
    value = fields.Float(required=True,
                         validate=validate.Range(min=0, min_inclusive=False))
    pin = fields.Integer(required=True,
                         validate=validate.Range(min=0, max=27))
    active_low = fields.Boolean(required=True)
    name = fields.String(required=True,
                         validate=validate.Regexp(r'[a-zA-Z][A-Za-z0-9]*',
                                                  error='Name must match the regex [a-zA-Z][A-Za-z0-9]*'))


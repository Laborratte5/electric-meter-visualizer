import json
from json.decoder import JSONDecodeError

from deprecated import deprecated

from flask import Flask, render_template, request, abort, make_response
from marshmallow import Schema, fields, ValidationError, validate, validates_schema

from ConfigLoader import Config
from Logic import Logic

app = Flask(__name__)
development_mode = app.config['ENV'] == 'development'

logic = Logic(Config.get_config(), development_mode)


@app.route('/')
def index():
    return render_template('index.html')


# Data API
# TODO refactor data api
@app.route('/data')
def data():
    return 'data'


@app.route('/data/raw')
def raw_data():
    request_data = RequestDataSchema().load(request.args)

    raw_data = logic.get_raw(request_data.get('since'), request_data.get('until'))

    data = PowerUsageData()
    data.power_usage = raw_data

    return DataSchema().dumps(data)


@app.route('/data/day')
def day_data():
    request_data = RequestDataSchema().load(request.args)

    raw_data = logic.get_day(request_data.get('since'), request_data.get('until'))

    data = PowerUsageData()
    data.power_usage = raw_data

    return DataSchema().dumps(data)


@app.route('/data/week')
def week_data():
    return 'week data'


@app.route('/data/month')
def month_data():
    request_data = RequestDataSchema().load(request.args)

    raw_data = logic.get_month(request_data.get('since'), request_data.get('until'))

    data = PowerUsageData()
    data.power_usage = raw_data

    return DataSchema().dumps(data)


@app.route('/data/year')
def year_data():
    request_data = RequestDataSchema().load(request.args)

    raw_data = logic.get_year(request_data.get('since'), request_data.get('until'))

    data = PowerUsageData()
    data.power_usage = raw_data

    return DataSchema().dumps(data)


@app.route('/data/years')
def years_data():
    request_data = RequestDataSchema().load(request.args)

    raw_data = logic.get_years(request_data.get('since'), request_data.get('until'))

    data = PowerUsageData()
    data.power_usage = raw_data

    return DataSchema().dumps(data)


# Electric meter API
@app.route('/electric-meter', methods=['GET'])
def get_electric_meter():
    meter_id = RequestElectricMeterSchema().load(request.args, partial=True).get('id')

    electric_meters = []

    # Supplied id means return only electric meter with this id
    if meter_id is not None:
        # Search for electric meter witch specific id
        try:
            # Wrap meter in list of (id, meter) tupel
            electric_meters = [(meter_id, logic.get_electric_meter(meter_id))]
        except KeyError:
            abort_meter_not_found('no electric meter with requested id exists')
        except ValueError:
            abort_meter_not_found('electric meter id must be a integer')
    # No id means return all electric meter
    else:
        electric_meters = logic.get_electric_meters()

    return {
        "total_number": len(electric_meters),
        "electric_meters": [electric_meter_to_dic(meter_id, electric_meter)
                            for meter_id, electric_meter in electric_meters]
    }


@app.route('/electric-meter', methods=['POST'])
def add_electric_meter():
    # Parse request
    meter_dict = AddElectricMeterSchema().load(json.loads(request.data))

    # Add new electric meter
    new_meter, id = logic.add_electric_meter(**meter_dict)

    json_response = {
        "new_meter": electric_meter_to_dic(id, new_meter)
    }

    return json_response, 201


@app.route('/electric-meter', methods=['DELETE'])
def delete_electric_meter():
    meter_id = RequestElectricMeterSchema().load(request.args).get('id')

    try:
        removed_meter = logic.remove_electric_meter(meter_id)
        return {
            'deleted_meter': electric_meter_to_dic(meter_id, removed_meter)
        }
    except KeyError:
        abort_meter_not_found('no electric meter with requested id exists')


@app.route('/electric-meter', methods=['PATCH'])
def change_electric_meter():
    meter_id = RequestElectricMeterSchema().load(request.args).get('id')

    # Test if meter with given id exists
    try:
        logic.get_electric_meter(meter_id)
    except KeyError:
        abort_meter_not_found('no electric meter with requested id exists')

    # Test if request contains payload with changes
    if not bool(request.data) or len(request.get_json().keys()) == 0:
        return '', 204

    changes = AddElectricMeterSchema().load(request.get_json(), partial=True)

    try:
        value = changes.get('value')
        pin = changes.get('pin')
        active_low = changes.get('active_low')
        name = changes.get('name')

        changed_meter = logic.change_electric_meter(meter_id, value, pin, active_low, name)

        if changed_meter is None:
            return '', 204

        return {
            'patched_meter': electric_meter_to_dic(meter_id, changed_meter)
        }
    except KeyError:
        abort_meter_not_found('no electric meter with requested id exists')


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    response = {
        'code': "INVALID_PARAMETER",
        'parameter': list(error.messages.keys()),
        'info': error.messages
    }

    return response, 400


# Helper functions
def abort_meter_not_found(info):
    make_error_response('ELECTRIC_METER_NOT_FOUND', info, error_code=404)


@deprecated()
def make_error_response(api_error_code, message, info=None, error_code=400):
    if info is None:
        info = {}

    response = make_response({
        'code': api_error_code,
        'message': message,
        'info': info
    }, error_code)

    abort(response)


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
                         validate=validate.Regexp(r'[a-zA-Z][A-Za-z0-9]*'))


class RequestElectricMeterSchema(Schema):
    id = fields.Integer(required=True, validate=validate.Range(min=0))


class RequestDataSchema(Schema):
    since = fields.DateTime()
    until = fields.DateTime()

    @validates_schema(skip_on_field_errors=True)
    def validate_request(self, data, **kwargs):
        until = data.get('until')
        since = data.get('since')
        if until is not None and since is not None and until < since:
            raise ValidationError('Since timestamp must be before until timestamp')


class PowerUsageDataSchema(Schema):
    timestamp = fields.DateTime()
    value = fields.Float()


class PowerUsageSchema(Schema):
    id = fields.Integer()
    value = fields.Float()
    pin = fields.Integer()
    active_low = fields.Boolean()
    name = fields.String()
    data = fields.List(fields.Nested(PowerUsageDataSchema))


class DataSchema(Schema):
    power_usage = fields.List(cls_or_instance=fields.Nested(PowerUsageSchema))


class PowerUsageData:

    def __init__(self):
        self.power_usage = []

    def append(self, electric_meter_data):
        self.power_usage.append(electric_meter_data)

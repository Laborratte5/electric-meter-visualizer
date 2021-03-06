import json
import os
import unittest
from datetime import datetime

import Webinterface
from ElectricMeterMockup import ElectricMeterMockup
from Logic import ElectricMeterData
from Webinterface import app


class LogicMock:

    def __init__(self):
        self._next_id = 10
        self.electric_meters = {}
        self.data_electric_meter_id = 0

    def add_electric_meter(self, value, pin, active_low, name):
        self._next_id += 1
        electric_meter = ElectricMeterMockup(value, pin, active_low, name)
        self.electric_meters[self._next_id] = electric_meter

        return electric_meter, self._next_id

    def remove_electric_meter(self, id):
        removed_meter = self.electric_meters[id]
        del self.electric_meters[id]
        return removed_meter

    def get_electric_meter(self, id):
        return self.electric_meters[id]

    def get_electric_meters(self):
        return self.electric_meters.items()

    def change_electric_meter(self, id, value=None, pin=None, active_low=None, name=None):
        electric_meter = self.electric_meters[id]

        if value == float(electric_meter.value) \
                and pin == electric_meter.pin \
                and active_low == electric_meter.active_low \
                and name == electric_meter.name:
            return None

        if value is not None:
            electric_meter.set_value(value)
        if pin is not None:
            electric_meter.set_pin(pin)
        if active_low is not None:
            electric_meter.set_active_low(active_low)
        if name is not None:
            electric_meter.set_name(name)

        return electric_meter

    def get_raw(self, since=None, until=None):
        meter = self.get_electric_meter(self.data_electric_meter_id)
        return [ElectricMeterData(self.data_electric_meter_id, meter, {self.data_electric_meter_id: [
            {'value': 100, 'timestamp': datetime(2021, 5, 8, 23, 30)},
            {'value': 200, 'timestamp': datetime(2021, 5, 8, 23, 45)},
            {'value': 300, 'timestamp': datetime(2021, 5, 9, 00, 00)},
            {'value': 400, 'timestamp': datetime(2021, 5, 9, 00, 15)},
            {'value': 500, 'timestamp': datetime(2021, 5, 9, 00, 30)}
        ]})]

    def get_day(self, since=None, until=None):
        meter = self.get_electric_meter(self.data_electric_meter_id)
        return [ElectricMeterData(self.data_electric_meter_id, meter, {self.data_electric_meter_id: [
            {'value': hour * 10, 'timestamp': datetime(2020, 10, hour//24 + 1, hour % 24, 00)} for hour in range(24)
        ]})]

    def get_month(self, since=None, until=None):
        meter = self.get_electric_meter(self.data_electric_meter_id)
        return [ElectricMeterData(self.data_electric_meter_id, meter, {self.data_electric_meter_id: [
            {'value': day * 10, 'timestamp': datetime(2020, day//30 + 3, day % 30 + 1, 00, 00)} for day in range(60)
        ]})]

    def get_year(self, since=None, until=None):
        meter = self.get_electric_meter(self.data_electric_meter_id)
        return [ElectricMeterData(self.data_electric_meter_id, meter, {self.data_electric_meter_id: [
            {'value': month * 10, 'timestamp': datetime(2020, month + 1, 1, 00, 00)} for month in range(12)
        ]})]

    def get_years(self, since=None, until=None):
        meter = self.get_electric_meter(self.data_electric_meter_id)
        return [ElectricMeterData(self.data_electric_meter_id, meter, {self.data_electric_meter_id: [
            {'value': year * 10, 'timestamp': datetime(year + 2020, 1, 1, 00, 00)} for year in range(3)
        ]})]

    def set_getDataElectricMeterId(self, meter_id):
        self.data_electric_meter_id = meter_id


class GetElectricMeterApiTest(unittest.TestCase):

    url = '/electric-meter'

    def setUp(self) -> None:
        if os.path.exists('database.json'):
            os.remove('database.json')

        self.logic_mock = LogicMock()
        Webinterface.logic = self.logic_mock
        app.config['TESTING'] = True
        self.app = app.test_client()

    def testGetElectricMeter_notFoundIdValue(self):
        # Test
        response = self.app.get(GetElectricMeterApiTest.url + '?id=' + '300')

        # Assert
        self.assertEqual(404, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('ELECTRIC_METER_NOT_FOUND', content['code'])
        self.assertEqual('no electric meter with requested id exists', content['message'])
        self.assertEqual({}, content['info'])

    def testGetElectricMeter_negativeId(self):
        # Test
        response = self.app.get(GetElectricMeterApiTest.url + '?id=' + '-1')

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['id']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testGetElectricMeter_notFoundIdType(self):
        # Test
        response = self.app.get(GetElectricMeterApiTest.url + '?id=' + 'INVALID')

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['id']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testGetElectricMeter_validId(self):
        meter, meter_id = self.addElectricMeterToLogicMock(4, 1, False, 'First Electric Meter', 3)

        # Test
        response = self.app.get(GetElectricMeterApiTest.url + '?id=' + str(meter_id))

        # Assert
        self.assertEqual(200, response.status_code)

        content = json.loads(response.data)
        self.assertEqual({
            'total_number': 1,
            'electric_meters': [
                {
                    'id': meter_id,
                    'name': meter.name,
                    'pin': meter.pin,
                    'active_low': meter.active_low,
                    'value': meter.value,
                    'current_value': meter.value * meter.count
                }
            ]
        }, content)

    def testGetElectricMeter_noMeters(self):
        # Test
        response = self.app.get(GetElectricMeterApiTest.url)

        # Assert
        self.assertEqual(200, response.status_code)

        content = json.loads(response.data)
        self.assertEqual(0, content['total_number'])
        self.assertEqual([], content['electric_meters'])

    def testGetElectricMeter_oneMeter(self):
        meter, meter_id = self.addElectricMeterToLogicMock(4, 1, False, 'only meter', 5)

        # Test
        response = self.app.get(GetElectricMeterApiTest.url)

        # Assert
        self.assertEqual(200, response.status_code)

        content = json.loads(response.data)
        self.assertEqual(1, content['total_number'])
        self.assertEqual([{
            'id': meter_id,
            'name': meter.name,
            'pin': meter.pin,
            'value': meter.value,
            'active_low': meter.active_low,
            'current_value': meter.count * meter.value
        }], content['electric_meters'])

    def testGetElectricMeter_twoMeter(self):
        meter1, meter1_id = self.addElectricMeterToLogicMock(4, 1, False, 'first meter', 5)
        meter2, meter2_id = self.addElectricMeterToLogicMock(12, 2, True, 'second meter', 3)

        # Test
        response = self.app.get(GetElectricMeterApiTest.url)

        # Assert
        self.assertEqual(200, response.status_code)

        content = json.loads(response.data)
        self.assertEqual(2, content['total_number'])
        self.assertEqual([
            {
                'id': meter1_id,
                'name': meter1.name,
                'pin': meter1.pin,
                'value': meter1.value,
                'active_low': meter1.active_low,
                'current_value': meter1.count * meter1.value
            },
            {
                'id': meter2_id,
                'name': meter2.name,
                'pin': meter2.pin,
                'value': meter2.value,
                'active_low': meter2.active_low,
                'current_value': meter2.count * meter2.value
            }
        ], content['electric_meters'])

    def testGetElectricMeter_oneOfTwo(self):
        meter1, meter1_id = self.addElectricMeterToLogicMock(4, 1, False, 'first meter', 5)
        self.addElectricMeterToLogicMock(12, 2, True, 'second meter', 3)

        # Test
        response = self.app.get(GetElectricMeterApiTest.url + '?id=' + str(meter1_id))

        # Assert
        self.assertEqual(200, response.status_code)

        content = json.loads(response.data)
        self.assertEqual(1, content['total_number'])
        self.assertEqual([
            {
                'id': meter1_id,
                'name': meter1.name,
                'pin': meter1.pin,
                'value': meter1.value,
                'active_low': meter1.active_low,
                'current_value': meter1.count * meter1.value
            }
        ], content['electric_meters'])

    def addElectricMeterToLogicMock(self, value, pin, active_low, name, meter_count):
        meter, meter_id = self.logic_mock.add_electric_meter(value, pin, active_low, name)
        meter.count = meter_count
        return meter, meter_id


class PostElectricMeterApiTest(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.exists('database.json'):
            os.remove('database.json')

        self.logic_mock = LogicMock()
        Webinterface.logic = self.logic_mock
        app.config['TESTING'] = True
        self.app = app.test_client()

    def testPostElectricMeter_badRequestInvalidParameter(self):
        # Test
        response = self.app.post('/electric-meter', json={
            'name': '',  # Empty name not allowed
            'value': 0,
            'pin': 50,
            'active_low': 'Truefdsa'
        })

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)

        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['name','value','pin','active_low']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testPostElectricMeter_badRequestMissingParameter(self):
        # Test
        response = self.app.post('/electric-meter', json={
            'name': 'test',
            # Missing value parameter
            'pin': 5,
            'active_low': True
        })

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(['value'], content['parameter'])
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info']:
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testPostElectricMeter_success(self):
        post_json = {
            'name': 'Name',
            'value': 10,
            'pin': 5,
            'active_low': True
        }
        # Test
        response = self.app.post('/electric-meter', json=post_json)

        # Assert
        self.assertEqual(201, response.status_code)

        content = json.loads(response.data)
        self.assertEqual({
            'id': 11,
            'name': 'Name',
            'value': 10.0,
            'pin': 5,
            'active_low': True,

            'current_value': 0.0
        }, content['new_meter'])


class DeleteElectricMeterApiTest(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.exists('database.json'):
            os.remove('database.json')

        self.logic_mock = LogicMock()
        Webinterface.logic = self.logic_mock
        app.config['TESTING'] = True
        self.app = app.test_client()

    def testDeleteElectricMeter_notFoundIdValue(self):
        response = self.app.delete('/electric-meter?id=' + '300')

        # Assert
        self.assertEqual(404, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('ELECTRIC_METER_NOT_FOUND', content['code'])
        self.assertEqual('no electric meter with requested id exists', content['message'])
        self.assertEqual({}, content['info'])

    def testDeleteElectricMeter_notFoundIdType(self):
        response = self.app.delete('/electric-meter?id=' + 'INVALID')

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['id']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testDeleteElectricMeter_badRequest(self):
        response = self.app.delete('/electric-meter')

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['id']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testDeleteElectricMeter_success(self):
        electric_meter, meter_id = self.logic_mock.add_electric_meter(4, 1, False, 'remove me')

        # Test
        response = self.app.delete('/electric-meter?id=' + str(meter_id))

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertNotIn(meter_id, self.logic_mock.electric_meters.keys())
        content = json.loads(response.data)
        self.assertEqual({
            'id': meter_id,
            'name': electric_meter.name,
            'pin': electric_meter.pin,
            'active_low': electric_meter.active_low,
            'value': electric_meter.value,

            'current_value': electric_meter.value * electric_meter.count
        }, content['deleted_meter'])


class PatchElectricMeterApiTest(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.exists('database.json'):
            os.remove('database.json')

        self.logic_mock = LogicMock()
        Webinterface.logic = self.logic_mock
        app.config['TESTING'] = True
        self.app = app.test_client()

    def testPatchElectricMeter_notModified(self):
        patch_json = {
            'name': 'Name',
            'value': 10,
            'pin': 5,
            'active_low': True
        }
        meter, meter_id = self.addElectricMeterToLogicMock(patch_json['value'],
                                         patch_json['pin'], patch_json['active_low'], patch_json['name'], 3)
        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json=patch_json)

        self.assertEqual(204, response.status_code)

    def testPatchElectricMeter_notModifiedEmptyRequest(self):
        meter, meter_id = self.addElectricMeterToLogicMock(3.0, 4, False, 'name', 3)

        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json={})

        self.assertEqual(204, response.status_code)

    def testPatchElectricMeter_noRequestBody(self):
        meter, meter_id = self.addElectricMeterToLogicMock(3.0, 4, False, 'name', 3)

        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id))

        self.assertEqual(204, response.status_code)

    def testPatchElectricMeter_badRequestNoId(self):
        # Test
        response = self.app.patch('/electric-meter', json={
            'name': 'Name2',
            'pin': 5
        })

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['id']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testPatchElectricMeter_badRequestInvalidChange(self):
        electric_meter, meter_id = self.addElectricMeterToLogicMock(1, 1, False, 'Name', 3)

        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json={
            'name': 'Name2',
            'pin': -5
        })

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['pin']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testPatchElectricMeter_badRequestChangeInvalidField(self):
        electric_meter, meter_id = self.addElectricMeterToLogicMock(1, 1, False, 'Name', 3)

        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json={
            'name': 'Name2',
            'current_value': -5
        })

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertListEqual(sorted(['current_value']), sorted(content['parameter']))
        self.assertListEqual(sorted(content['parameter']), sorted(list(content['info'].keys())))
        for info in content['info'].values():
            self.assertIsNotNone(info)
            self.assertNotEqual(len(info), 0)

    def testPatchElectricMeter_notFound(self):
        patch_json = {
            'name': 'Name2',
        }
        # Test
        response = self.app.patch('/electric-meter?id=' + '300', json=patch_json)

        # Assert
        self.assertEqual(404, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('ELECTRIC_METER_NOT_FOUND', content['code'])
        self.assertEqual('no electric meter with requested id exists', content['message'])
        self.assertEqual({}, content['info'])

    def testPatchElectricMeter_notFoundEmptyRequest(self):
        # Test
        response = self.app.patch('/electric-meter?id=' + '300', json={})

        # Assert
        self.assertEqual(404, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('ELECTRIC_METER_NOT_FOUND', content['code'])
        self.assertEqual('no electric meter with requested id exists', content['message'])
        self.assertEqual({}, content['info'])

    def testPatchElectricMeter_success(self):
        electric_meter, meter_id = self.addElectricMeterToLogicMock(1, 1, False, 'Name', 3)

        patch_name = 'Name2'
        patch_pin = 2
        patch_active_low = True

        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json={
            'name': patch_name,
            'pin': patch_pin,
            'active_low': patch_active_low
        })

        # Assert
        self.assertEqual(200, response.status_code)

        content = json.loads(response.data)
        self.assertEqual({
            'patched_meter': {
                'id': meter_id,
                'name': patch_name,
                'pin': patch_pin,
                'active_low': patch_active_low,
                'value': electric_meter.value,

                'current_value': electric_meter.value * electric_meter.count
            }
        }, content)

    def addElectricMeterToLogicMock(self, value, pin, active_low, name, meter_count):
        meter, meter_id = self.logic_mock.add_electric_meter(value, pin, active_low, name)
        meter.count = meter_count
        return meter, meter_id


class GetDataApiTest(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.exists('database.json'):
            os.remove('database.json')

        self.logic_mock = LogicMock()
        electric_meter, meter_id = self.logic_mock.add_electric_meter(2, 3, True, 'Electric-meter_1')
        self.logic_mock.set_getDataElectricMeterId(meter_id)
        self.electric_meter = electric_meter
        self.meter_id = meter_id
        Webinterface.logic = self.logic_mock
        app.config['TESTING'] = True
        self.app = app.test_client()

    def testGetDataRaw_noFilter(self):
        # Setup
        data = self.logic_mock.get_raw()[0].data
        # Test
        response = self.app.get('/data/raw')

        # Assert
        self.assertEqual(response.status_code, 200)
        self._assert_data(response, data)

    # TODO get raw day since until since-until invalid-since-until

    def testGetDataDay_noFilter(self):
        # Setup
        data = self.logic_mock.get_day()[0].data
        # Test
        response = self.app.get('/data/day')

        # Assert
        self.assertEqual(response.status_code, 200)
        self._assert_data(response, data)

    # TODO get data day since until since-until invalid-since-until

    def testGetDataMonth_noFilter(self):
        # Setup
        data = self.logic_mock.get_month()[0].data
        # Test
        response = self.app.get('/data/month')

        # Assert
        self.assertEqual(response.status_code, 200)
        self._assert_data(response, data)
    # TODO get data month since until since-until invalid-since-until

    def testGetDataYear_noFilter(self):
        # Setup
        data = self.logic_mock.get_year()[0].data
        # Test
        response = self.app.get('/data/year')

        # Assert
        self.assertEqual(response.status_code, 200)
        self._assert_data(response, data)

    # TODO get data month since until since-until invalid-since-until

    def testGetDataYears_noFilter(self):
        # Setup
        data = self.logic_mock.get_years()[0].data
        # Test
        response = self.app.get('/data/years')

        # Assert
        self.assertEqual(response.status_code, 200)
        self._assert_data(response, data)

    def _assert_data(self, response, data):
        expected_data = []
        for entry in data:
            expected_data.append({'value': entry['value'], 'timestamp': entry['timestamp'].isoformat()})

        self.assertEqual(json.loads(response.data), {
            'power_usage': [
                {
                    'id': self.meter_id,
                    'value': self.electric_meter.value,
                    'pin': self.electric_meter.pin,
                    'active_low': self.electric_meter.active_low,
                    'name': self.electric_meter.name,
                    'data': expected_data
                }
            ]
        })


if __name__ == '__main__':
    unittest.main()

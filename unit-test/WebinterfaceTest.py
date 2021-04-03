import json
import os
import unittest

import Webinterface
from ElectricMeterMockup import ElectricMeterMockup
from Webinterface import app


class LogicMock:

    def __init__(self):
        self._next_id = 10
        self.electric_meters = {}

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

        if value is not None:
            electric_meter.set_value(value)
        if pin is not None:
            electric_meter.set_pin(pin)
        if active_low is not None:
            electric_meter.set_active_low(active_low)
        if name is not None:
            electric_meter.set_name(name)

        return electric_meter

    def get_raw(self):
        raise NotImplemented
        # TODO
        pass

    def get_day(self, t_minus=0):
        raise NotImplemented
        # TODO
        pass

    def get_month(self, t_minus=0):
        raise NotImplemented
        # TODO
        pass

    def get_year(self, t_minus=0):
        raise NotImplemented
        # TODO
        pass

    def get_years(self):
        raise NotImplemented
        # TODO
        pass


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
        self.assertEqual('no electric meter with requested id exist', content['message'])
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
        meter, meter_id = self.addElectricMeterToLogicMock(patch_json['name'], patch_json['value'],
                                         patch_json['pin'], patch_json['active_low'], 3)
        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json=patch_json)

        self.assertEqual(304, response.status_code)

    def testPatchElectricMeter_badRequestNoId(self):
        # Test
        response = self.app.patch('/electric-meter', json={
            'name': 'Name2',
            'pin': 5
        })

        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('NO_ID_PROVIDED', content['code'])
        self.assertEqual('no id provided by request', content['message'])
        self.assertEqual({'parameter_name': 'id'}, content['info'])

    def testPatchElectricMeter_badRequestInvalidChange(self):
        electric_meter, meter_id = self.addElectricMeterToLogicMock('Name', 1, 1, False, 3)

        # Test
        response = self.app.patch('/electric-meter?id=' + str(meter_id), json={
            'name': 'Name2',
            'pin': -5
        })

        # Assert
        self.assertEqual(400, response.status_code)

        content = json.loads(response.data)
        self.assertEqual('INVALID_PARAMETER', content['code'])
        self.assertEqual('pin number out of range', content['message'])
        self.assertEqual({'parameter_name': 'pin'}, content['info'])

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
        self.assertEqual('no electric meter with requested id exist', content['message'])
        self.assertEqual({}, content['info'])

    def testPatchElectricMeter_success(self):
        electric_meter, meter_id = self.addElectricMeterToLogicMock('Name', 1, 1, False, 3)

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


if __name__ == '__main__':
    unittest.main()

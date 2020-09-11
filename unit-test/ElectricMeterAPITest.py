import json
import unittest
import itertools

#import requests
from Webinterface import app
import Webinterface


class ElectricMeterMock:

    def __init__(self, value=0, pin=0, active_low=False, name='mock'):
        self.value = value
        self.pin = pin
        self.active_low = active_low
        self.name = name
        self.count = 0

    def get_amount(self):
        return self.count * self.value

    def reset(self):
        self.count = 0

    def set_count(self, new_count):
        super().count = new_count


class LogicMock(object):

    def __init__(self, electric_meter):
        self.electric_meter = electric_meter

    def add_electric_meter(self, value, pin, active_low, name):
        return self.electric_meter, 0

    def remove_electric_meter(self, id):
        if id < 0:
            raise KeyError
        else:
            return self.electric_meter, 0

    def get_electric_meter(self, id):
        if id < 0:
            raise KeyError
        else:
            return self.electric_meter

    def get_electric_meters(self):
        pass

    def change_electric_meter(self, id, value=None, pin=None, active_low=None, name=None):
        if id < 0:
            raise KeyError
        else:
            return self.electric_meter


class ApiAccessibilityTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.api_url = "http://127.0.0.1:5000" + "/api/json" + "/electric-meter"

    def test_electric_meter_accessibility(self):
        #response = requests.get(self.api_url)
        response = self.app.get(self.api_url)
        self.assertNotEqual(response.status_code, 404)

    def test_inaccessible_url(self):
        #response = requests.get(self.api_url + "xxxxxxxxxxxxxxxxx")
        response = self.app.get(self.api_url + 'xxxxxxxxxxxxxxxxxxx')
        self.assertEqual(response.status_code, 404)


class AddElectricMeterTest(unittest.TestCase):
    def setUp(self):
        self.api_url = "/api/json" + "/electric-meter" + "/add"
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        self.app = app.test_client()
        Webinterface.logic = LogicMock(electric_meter=ElectricMeterMock())

    def test_electric_meter_add_accessibility(self):
        #response = requests.get(self.api_url)
        response = self.app.get(self.api_url)
        self.assertNotEqual(response.status_code, 404)

    # TODO maybe still too complex for unit test code???
    def test_electric_meter_add_missing_parameter(self):
        all_parameters = (('value', 1.3), ('pin', 1), ('active-low', False), ('name', "test"))
        """
        param_combinations = []
        for i in range(2**len(all_parameters)):
            bin_str = bin(i)[2:]
            while len(bin_str) < len(all_parameters):
                bin_str = '0' + bin_str
            param_arrangement = [all_parameters[i] for i in range(len(bin_str)) if bin_str[i] == '1']
            missing_parameter = [all_parameters[i][0] for i in range(len(bin_str)) if bin_str[i] == '0']
            param_combinations.append((param_arrangement, missing_parameter))

        for combination, missing in param_combinations:
        """
        for L in range(0, len(all_parameters) + 1):
            for combination in itertools.combinations(all_parameters, L):
                missing = [x[0] for x in all_parameters if x not in combination]
                query = ""
                for param, value in combination:
                    query += param + '=' + str(value) + '&'
                query = query[:-1]
                url = self.api_url + '?' + query
                response = self.app.get(url)
                if len(missing) > 0:
                    self.assertEqual(response.status_code, 400)
                    obj = json.loads(response.data)
                    # TODO check api code
                    self.assertListEqual(obj['parameters'], missing)
                else:
                    self.assertNotEqual(response.status_code, 400, response.data)

    def test_electric_meter_add_invalid_parameter_type(self):
        all_parameters = (('value', (1.3, "invalid")),
                          ('pin', (1, "invalid")),
                          ('active-low', (False, "invalid")))
        for i in range(2**len(all_parameters)):
            bin_str = bin(i)[2:]
            while len(bin_str) < len(all_parameters):
                bin_str = '0' + bin_str
            invalid_values = [(all_parameters[j][0], all_parameters[j][1][1])
                              for j in range(len(bin_str)) if int(bin_str[j]) == 1]
            valid_values = [(all_parameters[j][0], all_parameters[j][1][0])
                            for j in range(len(bin_str)) if int(bin_str[j]) == 0]
            query = ""
            for param, value in invalid_values:
                query += param + '=' + str(value) + '&'
            for param, value in valid_values:
                query += param + '=' + str(value) + '&'
            query += 'name=test'
            url = self.api_url + '?' + query
            response = self.app.get(url)
            if i != 0:
                self.assertEqual(400, response.status_code)
                obj = json.loads(response.data)
                response_missing = [obj['parameters'][i]['parameter'] for i in range(len(obj['parameters']))]
                # TODO check api code
                self.assertListEqual(response_missing, [name for name, value in invalid_values])
            else:
                self.assertNotEqual(400, response.status_code, response.data)

    def test_electric_meter_add_invalid_parameter_value(self):
        all_parameters = (('value', (1.3, -3)),
                          ('pin', (1, -4)))
        for i in range(2 ** len(all_parameters)):
            bin_str = bin(i)[2:]
            while len(bin_str) < len(all_parameters):
                bin_str = '0' + bin_str
            invalid_values = [(all_parameters[j][0], all_parameters[j][1][1])
                              for j in range(len(bin_str)) if int(bin_str[j]) == 1]
            valid_values = [(all_parameters[j][0], all_parameters[j][1][0])
                            for j in range(len(bin_str)) if int(bin_str[j]) == 0]
            query = ""
            for param, value in invalid_values:
                query += param + '=' + str(value) + '&'
            for param, value in valid_values:
                query += param + '=' + str(value) + '&'
            query += 'name=test&active-low=true'
            url = self.api_url + '?' + query
            response = self.app.get(url)
            if i != 0:
                self.assertEqual(400, response.status_code)
                obj = json.loads(response.data)
                response_missing = [obj['parameters'][i]['parameter'] for i in range(len(obj['parameters']))]
                # TODO check api code
                self.assertListEqual(response_missing, [name for name, value in invalid_values])
            else:
                self.assertNotEqual(400, response.status_code, response.data)


class RemoveElectricMeterTest(unittest.TestCase):
    def setUp(self):
        self.api_url = "http://127.0.0.1:5000" + "/api/json" + "/electric-meter" + "/remove"
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        self.app = app.test_client()
        Webinterface.logic = LogicMock(electric_meter=ElectricMeterMock())

    def test_electric_meter_remove_accessibility(self):
        response = self.app.get(self.api_url)
        self.assertNotEqual(response.status_code, 404)

    def test_electric_meter_remove_missing_parameter(self):
        response = self.app.get(self.api_url)
        obj = json.loads(response.data)
        self.assertEquals(["id"], obj['parameters'])

    def test_electric_meter_remove_invalid_parameter_type(self):
        response = self.app.get(self.api_url + '?id=X')
        obj = json.loads(response.data)
        self.assertTrue('id' in [info['parameter'] for info in obj['parameters']])

    def test_electric_meter_remove_invalid_parameter_value(self):
        invalid_id = -1
        response = self.app.get(self.api_url + '?id=' + str(invalid_id))
        obj = json.loads(response.data)
        self.assertEquals(400, obj['code'])
        self.assertEquals(invalid_id, obj['id'])


class ChangeElectricMeterTest(unittest.TestCase):
    def setUp(self):
        self.api_url = "http://127.0.0.1:5000" + "/api/json" + "/electric-meter" + "/change"
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        self.app = app.test_client()
        Webinterface.logic = LogicMock(ElectricMeterMock())

    def test_electric_meter_change_accessibility(self):
        response = self.app.get(self.api_url)
        self.assertNotEqual(response.status_code, 404)

    def test_electric_meter_change_missing_parameter(self):
        all_parameters = (('id', 1), ('value', 1.3), ('pin', 1), ('active-low', False), ('name', "test"))
        for L in range(0, len(all_parameters) + 1):
            for combination in itertools.combinations(all_parameters, L):
                missing = [x[0] for x in all_parameters if x not in combination]
                query = ""
                for param, value in combination:
                    query += param + '=' + str(value) + '&'
                query = query[:-1]
                url = self.api_url + '?' + query
                response = self.app.get(url)
                if len(missing) > 0:
                    self.assertEqual(response.status_code, 400)
                    obj = json.loads(response.data)
                    # TODO check api code
                    self.assertListEqual(obj['parameters'], missing)
                else:
                    self.assertNotEqual(response.status_code, 400, response.data)

    def test_electric_meter_change_invalid_parameter_type(self):
        all_parameters = (('value', (1.3, "invalid")),
                          ('pin', (1, "invalid")),
                          ('active-low', (False, "invalid")),
                          ('id', (1, -1)))
        for i in range(2**len(all_parameters)):
            bin_str = bin(i)[2:]
            while len(bin_str) < len(all_parameters):
                bin_str = '0' + bin_str
            invalid_values = [(all_parameters[j][0], all_parameters[j][1][1])
                              for j in range(len(bin_str)) if int(bin_str[j]) == 1]
            valid_values = [(all_parameters[j][0], all_parameters[j][1][0])
                            for j in range(len(bin_str)) if int(bin_str[j]) == 0]
            query = ""
            for param, value in invalid_values:
                query += param + '=' + str(value) + '&'
            for param, value in valid_values:
                query += param + '=' + str(value) + '&'
            query += 'name=test'
            url = self.api_url + '?' + query
            response = self.app.get(url)
            if i != 0:
                self.assertEqual(400, response.status_code)
                obj = json.loads(response.data)
                response_missing = [obj['parameters'][i]['parameter'] for i in range(len(obj['parameters']))]
                # TODO check api code
                self.assertListEqual(response_missing, [name for name, value in invalid_values])
            else:
                self.assertNotEqual(400, response.status_code, response.data)

    def test_electric_meter_change_invalid_parameter_value(self):
        pass


if __name__ == '__main__':
    unittest.main()

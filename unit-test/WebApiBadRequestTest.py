import unittest
import requests
import json

class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.baseURL = 'http://127.0.0.1:5000/'
        self.jsonApiURL = 'api/json/'

    # TODO
    def test_add_electric_meter_missing_all_parameters(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'electric-meter/add')
        obj = json.loads(response.content)
        self.assertEqual(400, response.status_code)
        self.assertEqual(400, obj['code'])
        self.assertEqual('missing parameters', obj['info'])
        self.assertEqual(['value', 'pin', 'active-low', 'name'], obj['missing_parameters'])

    def test_add_electric_meter_missing_parameter(self):
        # TODO
        expected_params = ['value', 'pin', 'active-low', 'name']
        for i in range(2**len(expected_params)):
            pass

        response = requests.get(self.baseURL + self.jsonApiURL + 'electric-meter/add?value=3')
        obj = json.loads(response.content)
        self.assertEqual(400, response.status_code)
        self.assertEqual(400, obj['code'])
        self.assertEqual('missing parameters', obj['info'])
        self.assertEqual(['pin', 'active-low', 'name'], obj['missing_parameters'])

if __name__ == '__main__':
    unittest.main()

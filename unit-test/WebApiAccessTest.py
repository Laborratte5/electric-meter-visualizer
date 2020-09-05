import unittest

from unittest import TestCase
import requests


class WebApiAccessTest(TestCase):

    def setUp(self):
        self.baseURL = 'http://33.33.33.33/'
        self.jsonApiURL = 'api/json/'

    def test_api_data(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'data')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_day(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'data/day')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_week(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'data/week')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_month(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'data/month')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_year(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'data/year')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'electric-meter')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter_add(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'electric-meter/add')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter_remove(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'electric-meter/remove')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter_change(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'electric-meter/change')
        self.assertNotEqual(response.status_code, 404)

    def test_api_database(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'database')
        self.assertNotEqual(response.status_code, 404)

    def test_api_database_add(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'database/add')
        self.assertNotEqual(response.status_code, 404)

    def test_api_database_remove(self):
        response = requests.get(self.baseURL + self.jsonApiURL + 'database/remove')
        self.assertNotEqual(response.status_code, 404)



if __name__ == '__main__':
    unittest.main()

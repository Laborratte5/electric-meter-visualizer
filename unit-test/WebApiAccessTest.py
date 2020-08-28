import unittest


from unittest import TestCase
import requests


class WebApiAccessTest(TestCase):

    def test_api_data(self):
        response = requests.get('http://127.0.0.1:5000/api/json/data')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_day(self):
        response = requests.get('http://127.0.0.1:5000/api/json/data/day')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_week(self):
        response = requests.get('http://127.0.0.1:5000/api/json/data/week')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_month(self):
        response = requests.get('http://127.0.0.1:5000/api/json/data/month')
        self.assertNotEqual(response.status_code, 404)

    def test_api_data_year(self):
        response = requests.get('http://127.0.0.1:5000/api/json/data/year')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter(self):
        response = requests.get('http://127.0.0.1:5000/api/json/electric-meter')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter_add(self):
        response = requests.get('http://127.0.0.1:5000/api/json/electric-meter/add')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter_remove(self):
        response = requests.get('http://127.0.0.1:5000/api/json/electric-meter/remove')
        self.assertNotEqual(response.status_code, 404)

    def test_api_electric_meter_change(self):
        response = requests.get('http://127.0.0.1:5000/api/json/electric-meter/change')
        self.assertNotEqual(response.status_code, 404)

    def test_api_database(self):
        response = requests.get('http://127.0.0.1:5000/api/json/database')
        self.assertNotEqual(response.status_code, 404)

    def test_api_database_add(self):
        response = requests.get('http://127.0.0.1:5000/api/json/database/add')
        self.assertNotEqual(response.status_code, 404)

    def test_api_database_remove(self):
        response = requests.get('http://127.0.0.1:5000/api/json/database/remove')
        self.assertNotEqual(response.status_code, 404)



if __name__ == '__main__':
    unittest.main()

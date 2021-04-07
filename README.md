# electric-meter-visualizer
A program run on a Raspberry Pi which aims to visualize the power consumption over time using a sensor that counts how often the wheel of an electric meter has turned in a specified period of time

# Configuration

# API
The API of the electric-meter-visualizer is split into two parts.
1. The Data API  
1. The Electric Meter API

## Data API
This API is used to retrieve measured data  
__TODO__

## Electric Meter API
This API is used to configure (add/remove/update) electric meter sensors.
It uses the endpoint `/electric-meter`
1. Add a new electric meter  
To add a electric meter
```http
POST /electric-meter
```
with the payload
```json
{
  "name": "<the name of the electric meter>",
  "value": <the amount of kwh one turn of the wheel corresponds to>,
  "pin": <the bcm pin number of the connection at the raspberry pi>,
  "active-low": <wether the pin should be treated as active low or not>
}
```
The Server replies with either a `201 CREATED` and a json object representing the new added electric meter
```json
{
  "new_meter": {
    "id": <the id of the newly created electric meter>,
    "name": "<the name of the electric meter>",
    "value": <the amount of kwh one turn of the wheel corresponds to>,
    "pin": <the bcm pin number of the connection at the raspberry pi>,
    "active-low": <wether the pin should be treated as active low or not>
    
    "current_value": <the amount of used electricity since the last reset of this electric meter>
  }
}
```
1. Delete a electric meter

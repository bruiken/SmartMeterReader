# SmartMeterReader
SmartMeterReader is a default Python 3 based reader to work with the [SmartMeterServer](https://github.com/bruiken/SmartMeterServer). It can be run on for example a Raspberry Pi, which can be connected to a Smart meter using a USB to RJ11 cable. The meter simply reads out data every second and submits it to RabbitMQ (for live data viewing) and every 5 minutes (configurable), it submits data to the server for historical data viewing.

## Installation
Installing Raspbian Lite comes with Python 3, so it is advised to use that. Then the requirements can be installed via `python3 -m pip install -r requirements.txt`. A config.json should be placed in the same directory as the python files and should contain the following information:  
 - `location_id`: should match the location id of this installation in the server.
 - `api_url`: fill in the full URL to the data endpoint of the server (`[base_url]/api/Data`).
 - `jwt_token`: generate in the server, note that regenerating a JWT token invalidates the old one.
 - `report_api_seconds` (optional, default=300): every how many seconds should the reader deliver historical data to the api endpoint.
 - `port` (optional, default="COM1"): port to which the meter is connected.
 - `baudrate` (optional, default=115200): baudrate of connection.
 - `parity` (optional, default="N"): parity settings of connection.
 - `stopbits` (optional, default=1): number of stopbits of connection.
 - `bytesize` (optional, default=8): byte size of connection.
 - `timeout` (optional, default=5): timeout of connection.
 - `rabbitmq_host`: Hostname of RabbitMQ endpoint.
 - `rabbitmq_port`: Port of RabbitMQ endpoint.
 - `rabbitmq_username`: Username of RabbitMQ user.
 - `rabbitmq_password`: Password of RabbitMQ user.
 - `rabbitmq_exchange`: Exchange name of RabbitMQ endpoint.
 - `rabbitmq_vhost`: Vhost of RabbitMQ endpoint.

Installing RabbitMQ is explained in more depth on its website. Note that RabbitMQ Web Stomp should be installed, because we are using it on the web.

from smartreader import SmartReader
import pika
import json
import datetime
import requests


class DataCollector:
    def __init__(self, config_path: str):
        self.config = DataCollector.read_config(config_path)
        self.smartreader = SmartReader(config_path)
        self.rmq_conn, self.rmq_channel = self.create_rabbitmq_connection()
        self.latest_api_report = datetime.datetime.min

    @staticmethod
    def read_config(config_path: str) -> dict:
        with open(config_path) as file:
            config_str = file.read()
            return json.loads(config_str)

    def create_rabbitmq_connection(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config['rabbitmq_host'],
                port=self.config['rabbitmq_port'],
                credentials=pika.PlainCredentials(
                    username=self.config['rabbitmq_username'],
                    password=self.config['rabbitmq_password']
                )))
        channel = connection.channel()
        channel.exchange_declare(
            exchange=self.config['rabbitmq_exchange'],
            exchange_type='topic')
        return connection, channel

    def report_electricity_rabbitmq(self, datagram):
        data = {
            'kw_usage': datagram.kw_usage_total,
            'kw_generated': datagram.kw_generated_total,
            'time': datagram.utc_timestamp,
        }
        loc_id = self.config['location_id']
        self.rmq_conn.process_data_events()
        self.rmq_channel.basic_publish(
            self.config['rabbitmq_exchange'],
            routing_key=f'{loc_id}.electricity',
            body=json.dumps(data)
        )

    def should_report_electricity_api(self):
        utcnow = datetime.datetime.utcnow()
        seconds_between_reports = self.config.get('report_api_seconds', 300)
        timedelta = datetime.timedelta(seconds=seconds_between_reports)
        return utcnow - timedelta >= self.latest_api_report

    def report_electricity_api(self, datagram):
        new_time = datetime.datetime.utcnow()
        url = self.config['api_url']
        token = self.config['jwt_token']
        data = {
            'KwhInT1': datagram.kwh_to_client_t1,
            'KwhInT2': datagram.kwh_to_client_t2,
            'KwhOutT1': datagram.kwh_from_client_t1,
            'KwhOutT2': datagram.kwh_from_client_t2,
            'GasReadout': datagram.last_gas_reading,
            'Time': datagram.time_utc
        }
        json_data = json.dumps(data, default=str)
        headers = {
            'Authentication': f'Bearer {token}'
        }
        r = requests.post(url, data=json_data, headers=headers)
        if r.status_code == 200:
            self.latest_api_report = new_time

    def meter_data_callback(self, datagram):
        self.report_electricity_rabbitmq(datagram)
        if self.should_report_electricity_api():
            self.report_electricity_api(datagram)

    def start_reading(self):
        try:
            self.smartreader.read_telegrams(
                callback_func=self.meter_data_callback
            )
        except Exception as ex:
            if self.rmq_conn.is_open:
                self.rmq_conn.close()
            raise ex

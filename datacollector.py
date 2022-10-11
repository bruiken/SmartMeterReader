from smartreader import SmartReader
import pika
import json


class DataCollector:
    def __init__(self, config_path: str):
        self.config = DataCollector.read_config(config_path)
        self.smartreader = SmartReader(config_path)
        self.rmq_conn, self.rmq_channel = self.create_rabbitmq_connection()

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
            exchange_type='direct')
        return connection, channel

    def report_electricity_rabbitmq(self, datagram):
        data = {
            'kw_usage': datagram.kw_usage_total,
            'kw_generated': datagram.kw_generated_total,
        }
        loc_id = self.config['location_id']
        self.rmq_channel.basic_publish(
            self.config['rabbitmq_exchange'],
            routing_key=f'{loc_id}.electricity',
            body=json.dumps(data)
        )

    def start_reading(self):
        try:
            self.smartreader.read_telegrams(
                callback_func=self.report_electricity_rabbitmq
            )
        except Exception as ex:
            if self.rmq_conn.is_open:
                self.rmq_conn.close()
            raise ex

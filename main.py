import serial
import json


class ConnectionIsClosedException(Exception):
    pass


class SmartReader:
    def __init__(self, config_path: str):
        self.config = SmartReader.read_config(config_path)

    @staticmethod
    def read_config(config_path: str) -> dict:
        with open(config_path) as file:
            config_str = file.read()
            return json.loads(config_str)

    def open_serial_connection(self) -> serial.Serial:
        return serial.Serial(
            port = self.config.get('port', 'COM1'),
            baudrate = self.config.get('baudrate', 115200),
            parity = self.config.get('parity', serial.PARITY_NONE),
            stopbits = self.config.get('stopbits', serial.STOPBITS_ONE),
            bytesize = self.config.get('bytesize', serial.EIGHTBITS),
            timeout = self.config.get('timeout', 5)
        )

    @staticmethod
    def read_one_line(conn: serial.Serial) -> str:
        if conn.isOpen():
            return conn.readline().decode('ascii')
        else:
            raise ConnectionIsClosedException()

    @staticmethod
    def scroll_to_start(conn: serial.Serial) -> str:
        if conn.isOpen():
            line = SmartReader.read_one_line(conn)
            while not line.startswith('/'):
                line = SmartReader.read_one_line(conn)
            return line
        else:
            raise ConnectionIsClosedException()

    def read_one_telegram(self) -> str:
        with self.open_serial_connection() as conn:
            SmartReader.scroll_to_start()
            line = SmartReader.read_one_line(conn)
            while not line.startswith('!'):
                print(line)


if __name__ == '__main__':
    reader = SmartReader('config.json')
    reader.read_one_telegram()

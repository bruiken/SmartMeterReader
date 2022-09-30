import serial
import json
from dataclasses import dataclass, field
from datetime import datetime
import re
from zoneinfo import ZoneInfo


REGEX_SINGLE_VAL = re.compile(r'^(?P<id>\d-\d:\d+\.\d+\.\d+)\((?P<data>[^\)]+)\)$')
REGEX_DOUBLE_VAL = re.compile(r'^(?P<id>\d-\d:\d+\.\d+\.\d+)\((?P<fdata>[^\)]+)\)\((?P<sdata>[^\)]+)\)$')
LOCAL_TIMEZONE = ZoneInfo('Europe/Amsterdam')
UTC_TIMEZONE = ZoneInfo('UTC')

class ConnectionIsClosedException(Exception):
    pass


@dataclass
class SmartMeterData:
    timestamp: str
    kwh_to_client_t1: float
    kwh_to_client_t2: float
    kwh_from_client_t1: float
    kwh_from_client_t2: float
    kw_to_client: float
    kw_from_client: float
    kw_usage_phase1: float
    kw_usage_phase2: float
    kw_usage_phase3: float
    kw_generated_phase1: float
    kw_generated_phase2: float
    kw_generated_phase3: float
    timestamp_gas: str
    last_gas_reading: float
    utc_timestamp: str = field(init=False)
    utc_timestamp_gas: str = field(init=False)

    def __post_init__(self):
        local_timestamp = datetime.strptime(self.timestamp[:-1], '%y%m%d%H%M%S', tzinfo=LOCAL_TIMEZONE)
        self.utc_timestamp = str(local_timestamp.astimezone(UTC_TIMEZONE))
        local_timestamp_gas = datetime.strptime(self.timestamp_gas[:-1], '%y%m%d%H%M%S', tzinfo=LOCAL_TIMEZONE)
        self.utc_timestamp_gas = str(local_timestamp_gas.astimezone(UTC_TIMEZONE))


IDENTIFIER_MAPPING = {
    '0-0:1.0.0': 'timestamp',
    '1-0:1.8.1': 'kwh_to_client_t1',
    '1-0:1.8.2': 'kwh_to_client_t2',
    '1-0:2.8.1': 'kwh_from_client_t1',
    '1-0:1.7.0': 'kw_to_client',
    '1-0:2.7.0': 'kw_from_client',
    '1-0:21:7.0': 'kw_usage_phase1',
    '1-0:41:7.0': 'kw_usage_phase2',
    '1-0:61:7.0': 'kw_usage_phase3',
    '1-0:22:7.0': 'kw_generated_phase1',
    '1-0:42:7.0': 'kw_generated_phase2',
    '1-0:62:7.0': 'kw_generated_phase3',
    'GAS_DATA': '0-1:24.2.1',
}


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
            line_bytes = conn.readline()
            line_ascii = line_bytes.decode('ascii')
            line_cleaned = line_ascii.strip('\r\n')
            return line_cleaned
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

    def read_telegram_lines(self) -> list:
        with self.open_serial_connection() as conn:
            line = SmartReader.scroll_to_start(conn)
            datalines = [line]
            line = SmartReader.read_one_line(conn)
            while not line.startswith('!'):
                datalines.append(line)
                line = SmartReader.read_one_line(conn)
            datalines.append(line)
        return datalines

    def read_telegram(self) -> SmartMeterData:
        data_lines = self.read_telegram_lines()
        return self.parse_telegram(data_lines)
    
    def parse_telegram(self, data_lines: list) -> SmartMeterData:
        full_data = dict()
        for line in data_lines:
            if match := REGEX_SINGLE_VAL.fullmatch(line):
                identifier, data = match.groups()
                if identifier in IDENTIFIER_MAPPING:
                    local_identifier = IDENTIFIER_MAPPING[identifier]
                    if local_identifier != 'timestamp':
                        data = float(data.split('*')[0])
                    full_data[local_identifier] = data
            elif match := REGEX_DOUBLE_VAL.fullmatch(line):
                identifier, data1, data2 = match.groups()
                if identifier == IDENTIFIER_MAPPING['GAS_DATA']:
                    float_data = float(data2.split('*')[0])
                    full_data['timestamp_gas'] = data1
                    full_data['last_gas_reading'] = float_data
        return SmartMeterData(**full_data)


if __name__ == '__main__':
    reader = SmartReader('config.json')
    data = reader.read_telegram()
    print(data.timestamp)
    print('kW delivered:', data.kw_to_client)
    print('kW generated:', data.kw_from_client)

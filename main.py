import sys
from datacollector import DataCollector


if __name__ == '__main__':
    configfile = 'config.json'
    if len(sys.argv) == 2:
        configfile = sys.argv[1]
    collector = DataCollector(configfile)
    collector.start_reading()

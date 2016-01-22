#!/usr/bin/env python

import psutil
import sys
import yaml
from optparse import OptionParser
import os
import threading
import logging
import httplib
import json

__author__ = 'liqin'


class Prober(threading.Thread):
    def __init__(self, conf, logger):
        threading.Thread.__init__(self)

        self.conf = conf
        self.logger = logger

        self.net_recv = 0
        self.net_sent = 0

        # A event to notify the thread that it should finish up and exit
        self.finished_event = threading.Event()

    def run(self):
        try:
            while not self.finished_event.is_set():
                result = self.__probing()
                self.__post_result_to_supervisor(result)
                self.finished_event.wait(self.conf['prober']['interval'])
        except Exception as e:
            self.logger.error('%s' % e)

    def __probing(self):
        system = self.__probe_system()
        services = self.__probe_services()

        result = {'system': system, 'services': services}
        return result

    def __probe_system(self):
        system = {'cpu': {}, 'memory': {}, 'disk': {}, 'net': {}}

        system['name'] = self.conf['host']['name']
        system['ip'] = self.conf['host']['ip']

        # cpu usage
        system['cpu']['count'] = psutil.cpu_count(logical=False)
        system['cpu']['percent'] = psutil.cpu_percent()

        self.logger.debug('cpu: %s' % system['cpu'])

        # memory usage
        memory = psutil.virtual_memory()
        system['memory']['total'] = memory[0]
        system['memory']['percent'] = memory[2]
        system['memory']['used'] = memory[3]
        system['memory']['free'] = memory[4]

        self.logger.debug('memory: %s' % system['memory'])

        # disk usage
        disk_usage = psutil.disk_usage('/')
        system['disk']['total'] = disk_usage.total

        disk_io = psutil.disk_io_counters(perdisk=False)
        system['disk']['io'] = {}
        system['disk']['io']['read_count'] = disk_io[0]
        system['disk']['io']['write_count'] = disk_io[1]
        system['disk']['io']['read_bytes'] = disk_io[2]
        system['disk']['io']['write_bytes'] = disk_io[3]

        self.logger.debug('disk: %s' % system['disk'])

        # net usage
        system['net']['connections_count'] = len(psutil.net_connections())

        net_io = psutil.net_io_counters(pernic=True)

        net_out_rate = 0
        net_in_rate = 0

        if self.net_recv != 0 and self.net_sent != 0:
            net_out_rate = net_io['eth0'][0] - self.net_sent
            net_in_rate = net_io['eth0'][1] - self.net_recv

            interval = self.conf['prober']['interval']
            net_in_rate = net_in_rate / (1024.00 * interval) # KB/S
            net_out_rate = net_out_rate / (1024.00 * interval) # KB/S

        system['net']['out_rate'] = net_out_rate
        system['net']['in_rate'] = net_in_rate
        system['net']['bytes_sent'] = net_io['eth0'][0]
        system['net']['bytes_recv'] = net_io['eth0'][1]
        system['net']['packets_sent'] = net_io['eth0'][2]
        system['net']['packets_recv'] = net_io['eth0'][3]

        self.net_sent = net_io['eth0'][0]
        self.net_recv = net_io['eth0'][1]

        self.logger.debug(('In: %.2f KB/S, Out: %.2f KB/S') % (net_in_rate, net_out_rate))
        self.logger.debug('net: %s' % system['net'])

        return system

    def __probe_services(self):
        services = []
        for svc in self.conf['services']:
            svc_result = {}

            svc_result['id'] = svc['id']
            svc_result['name'] = svc['name']

            svc_process = self.__get_process_by_service_name(svc['name'])
            if not svc_process:
                svc_result['live'] = False
                services.append(svc_result)
                continue
            else:
                svc_result['live'] = True
                svc_result['cpu_percent'] = svc_process.cpu_percent()
                svc_result['memory_percent'] = svc_process.memory_percent()

                mem_info_ex = svc_process.memory_info_ex()
                svc_result['virtual_memory_size'] = mem_info_ex[1]
                svc_result['shared_memory_size'] = mem_info_ex[2]

                try:
                    self.logger.info('%d' % len(svc_process.connections('tcp4')))
                except Exception as e:
                    pass

                services.append(svc_result)

        return services

    def __get_process_by_service_name(self, svc_name):

        for p in psutil.process_iter():
            if p.name() == svc_name:
                return p

        return

    def __post_result_to_supervisor(self, result):
        try:
            conn = httplib.HTTPConnection(self.conf['supervisor']['host'], port=self.conf['supervisor']['port'])

            req_headers = {"Content-type": "application/json", "charset": "UTF-8"}
            req_body = json.dumps(result)

            conn.request("POST", "/v1/results?type=xxx", body=req_body, headers=req_headers)

            response = conn.getresponse()
            print response.status, response.reason

            data = response.read()
            print data

            conn.close()
        except Exception as e:
            self.logger.error('%s' % e)


def initLogger(conf):
    # create logger
    logger = logging.getLogger("prober")
    logger.setLevel(conf['prober']['logLevel'])

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    return logger


def main():
    usage = 'usage: %prog [options]'
    parser = OptionParser(usage, version='%prog 1.0')
    parser.add_option('-c', '--config', dest='config', help='config file')

    options, args = parser.parse_args()
    if not options.config:
        parser.print_help()
        return 1

    try:
        conf_file = os.path.join(os.path.abspath('.'), options.config)

        with open(conf_file) as f:
            conf = yaml.load(f)
    except Exception as e:
        parser.error('%s' % e)
        return 1

    print conf
    logger = initLogger(conf)
    try:
        logger.info('Start probing...')

        # create prober and start it
        prober = Prober(conf, logger)
        prober.start()

        # wait for finished
        while prober.is_alive():
            prober.join(500)

    except KeyboardInterrupt:
        logger.info('Stop probing...')
        prober.finished_event.set()

    except Exception as e:
        logger.error('%s' % e)

    return


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/python

import rclpy
from rclpy.node import Node
from datetime import datetime

from rtcm_msgs.msg import Message

from base64 import b64encode
from threading import Thread

from http.client import HTTPConnection, IncompleteRead, HTTPResponse

''' This is to fix the IncompleteRead error
    http://bobrochel.blogspot.com/2010/11/bad-servers-chunked-encoding-and.html'''

def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except IncompleteRead as e:
            return e.partial
    return inner
HTTPResponse.read = patch_http_response_read(HTTPResponse.read)

class ntripconnect(Thread):
    def __init__(self, ntc):
        super(ntripconnect, self).__init__()
        self.ntc = ntc
        self.stop = False

    def run(self):
        authorization_str = self.ntc.ntrip_user + ':' + str(self.ntc.ntrip_pass)
        authorization_bytes = authorization_str.encode("utf-8")
        headers = {
            'Ntrip-Version': 'Ntrip/2.0',
            'User-Agent': 'NTRIP ntrip_ros',
            'Connection': 'close',
            'Authorization': 'Basic ' + str(b64encode(authorization_bytes))
        }
        connection = HTTPConnection(self.ntc.ntrip_server)
        connection.request('GET', '/'+self.ntc.ntrip_stream, self.ntc.nmea_gga, headers)
        response = connection.getresponse()
        if response.status != 200: raise Exception("blah")
        rmsg = Message()
        restart_count = 0
        while not self.stop:
            '''
            data = response.read(100)
            pos = data.find('\r\n')
            if pos != -1:
                rmsg.message = buf + data[:pos]
                rmsg.header.seq += 1
                rmsg.header.stamp = rospy.get_rostime()
                buf = data[pos+2:]
                self.ntc.pub.publish(rmsg)
            else: buf += data
            '''

            ''' This now separates individual RTCM messages and publishes each one on the same topic '''
            data = response.read(1)
            buf = bytearray()
            if len(data) != 0:
                if data[0] == 211:
                    buf.extend(data)
                    data = response.read(2)
                    buf.extend(data)
                    cnt = data[0] * 256 + data[1]
                    data = response.read(2)
                    buf.extend(data)
                    typ = (data[0] * 256 + data[1]) / 16
                    self.ntc.get_logger().info(f'date, cnt, type: {datetime.now()} , {cnt}, {int(typ)}')
                    cnt = cnt + 1
                    for x in range(cnt):
                        data = response.read(1)
                        buf.extend(data)
                    rmsg.message = buf
                    rmsg.header.stamp = self.ntc.get_clock().now().to_msg()
                    self.ntc.pub.publish(rmsg)
                else: self.ntc.get_logger.info(f'data received: {data}')
            else:
                ''' If zero length data, close connection and reopen it '''
                restart_count = restart_count + 1
                self.ntc.get_logger().info(f'Zero length, {restart_count}')
                connection.close()
                connection = HTTPConnection(self.ntc.ntrip_server)
                connection.request('GET', '/'+self.ntc.ntrip_stream, self.ntc.nmea_gga, headers)
                response = connection.getresponse()
                if response.status != 200: raise Exception("blah")

        connection.close()

class NtripClient(Node):
    def __init__(self):
        super().__init__('ntripclient')
        self.declare_parameters(
            namespace='',
            parameters = [
                ('ntrip_server', 'rtk2go.com:2101'),
                ('ntrip_user', 'USER'),
                ('ntrip_pass', 'PASS'),
                ('ntrip_stream', 'jemsundabase'),
                ('nmea_gga', '$GPGGA,130414.090,5824.333,N,01539.236,E,1,12,1.0,0.0,M,0.0,M,,*65')
            ])

        self.pub = None
        # Get parameter values
        self.rtcm_topic = "rtcm"
        self.ntrip_server = self.get_parameter('ntrip_server').value
        self.ntrip_user = self.get_parameter('ntrip_user').value
        self.ntrip_pass = self.get_parameter('ntrip_pass').value
        self.ntrip_stream = self.get_parameter('ntrip_stream').value
        self.nmea_gga = self.get_parameter('nmea_gga').value
        self.pub = self.create_publisher(Message, self.rtcm_topic, 10)
        self.get_logger().info(f'connecting to server: {self.ntrip_server}')
        self.connection = None
        self.connection = ntripconnect(self)
        self.connection.start()

    def run(self):
        rclpy.spin(self)
        if self.connection is not None:
            self.connection.stop = True

def main(args=None):
    rclpy.init(args=args)
    c = NtripClient()
    c.run()
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    c.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()


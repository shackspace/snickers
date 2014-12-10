#!/usr/bin/python3
import serial
from time import time
import socket

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.serialport import SerialPort


class Echo(protocol.Protocol):
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        global port
        print('Data Received and forwarding \'{}\''.format(data.strip()))
        self.transport.write(data)
        port.write(data)


class ReaderProtocol(LineReceiver):
    def connectionMade(self):
        print("Connected to serial port")

    def lineReceived(self, line):
        try:
            ident = line.split()[1]
            print("updating graphite for {}".format(ident))
            foreach_graphite(ident)
        except IndexError as i:
            print('cannot split message "{}"'.format(line))

port = SerialPort(ReaderProtocol(), '/dev/ttyUSB0', reactor, baudrate=9600)

factory = protocol.ServerFactory()
factory.protocol = Echo
reactor.listenTCP(5007,factory)

def to_graphite(l,host='heidi.shack',port=2003):
    """ l <= [ (path,value,epoch-timestamp),(...) ]
    """
    import socket
    data =""
    sock = socket.socket()
    for x in l:
        data+="{} {} {}\n".format(x[0],x[1],x[2])
    sock.connect((host, port))
    sock.sendall(data.encode())
    sock.close()
    #echo "$1 ${2} ${3:-$now}" | nc $GRAPHITE_HOST $GRAPHITE_PORT

def foreach_graphite(ident):
    # add an entry for the given id for the next 50 seconds
    now=int(time())
    data=[('sensors.motion.id.%s'%ident,'1',now+i) for i in range(50)]
    to_graphite(data)
    return data

reactor.run()

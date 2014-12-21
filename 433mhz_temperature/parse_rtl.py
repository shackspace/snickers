#!/usr/bin/python
from subprocess import Popen,PIPE
import signal
import traceback
from os import kill
from sys import exit
import logging as log
log.basicConfig(level=log.DEBUG)

pid = None
def signal_handler(signal, frame):
  global pid
  print('Killing Child %s'%pid)
  kill(pid,9)
  exit(0)

from time import time
import socket
import redis
redis_host='shackles.shack'
redis_port=6379
redis_db=0
r = redis.StrictRedis(host=redis_host, port=redis_port , db=redis_db)
def all_graphite(arr,host="heidi.shack",port=2003):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, port))
  msg=""
  for l in arr:
    path = l[0]
    data = l[1]
    try: ts = int(l[2])
    except: ts = int(time())
    msg+="%s %s %d\n"%(path,data,ts)
  log.info(msg)
  s.sendall(msg)
  s.close()

def send_redis(path,data,ts):
  try: ts = int(ts)
  except: ts = int(time())
  log.debug("hmset %s %d %s"%(path,ts,data))
  r.hmset(path,{str(ts):data})

def to_graphite(path,data,ts=None,host="heidi.shack",port=2003):
  #send_redis(path,data,ts)
  all_graphite([(path,data,ts)],host,port)
  
def main():
  global pid
  cmd = Popen(["/opt/rtl_433/build/src/rtl_433"], stdout=PIPE,stderr=PIPE,stdin=PIPE)
  temp = -1
  """
  button        = 0
  battery       = Ok
  temp          = 31.1
  humidity      = 18
  channel       = 1
  id            = 5
  rid           = 103
  hrid          = 67
  """
  pid = cmd.pid
  temp = -1
  battery = None
  humidity = -1
  for line in iter(cmd.stderr.readline, b''):
    log.debug("received: %s" %line.rstrip("\n"))
    if line.startswith("button"):
      button = line.split(" ")[-1].strip()
    if line.startswith("battery"):
      battery= line.split(" ")[-1].strip()
    elif line.startswith("temp"):
      temp = line.split(" ")[-1].strip()
      log.debug(line.rstrip("\n"))
    elif line.startswith("humidity"):
      humidity = line.split(" ")[-1].strip()
    elif line.startswith("rid"):
      rid = int(line.split(" ")[-1],16)
    elif line.startswith("channel"):
      channel = int(line.split(" ")[-1],16)
    elif line.startswith("id"):
      ident = int(line.split(" ")[-1],16)
    elif line.startswith("hrid"):
      hrid = int(line.split(" ")[-1],16)
      log.debug(ident)
      if ident == 5:
        all_graphite([
        #("sensors.temp.rooms.lounge.button",button),
        #("sensors.temp.rooms.lounge.battery",battery),
        ("sensors.temp.rooms.lounge.temp",temp),
        ("sensors.temp.rooms.lounge.humidity",humidity),
        #("sensors.temp.rooms.lounge.channel",channel),
        #("sensors.temp.rooms.lounge.id",ident),
        #("sensors.temp.rooms.lounge.rid",rid),
        #("sensors.temp.rooms.lounge.hrid",hrid)
        ])

  cmd.wait()

if __name__ == "__main__":
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGSEGV, signal_handler)
  signal.signal(signal.SIGCHLD, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  log.debug("startup")
  try:
    main()
  except Exception as e:
    log.error("Something erroered, bailing out")
    log.error(traceback.format_exc())
    signal_handler(0,0)

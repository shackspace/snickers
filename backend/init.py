#!/usr/bin/python

from flask import Flask,Response
from time import time
from datetime import datetime,timedelta
import requests
import json
app = Flask(__name__)
import redis
redis_host='glados.shack'
redis_port=6379
redis_db=0
sensor_namespace='sensors.motion.id.{}'
# sortierung raum <=> id
rooms_namespace='sensors.rooms.{}'
temperature_target='sensors.temp.rooms.lounge.temp'
timeout=timedelta(seconds=40)
point_value=60
graphite_host="http://heidi:8080"
CARBON_HOST="localhost"
CARBON_PORT=2003
simple_sensor_mapping = {
			"werkstatt":"7151202",
			"rz":"9846210",
			"medialab":"817506",
			"krebslounge":"5798242",
			"seminarraum":"11253282",
			"lounge":"2956898",
			"kueche":"3701090",
			"or1":"9018978",
			"or2":"2037282",
			"or3":"12492386",
			"or4":"16353218"
        }
import logging as log
log.basicConfig(level=log.DEBUG)
r = redis.StrictRedis(host=redis_host, port=redis_port , db=redis_db)

def data_from_graphite(target,addn_params=None):
    """
    target is a graphite data namespace like: 'sensors.motion.id.1'
    addn_params are additional targets which are added onto the graphite query
    """
    from urllib.parse import urlencode
    params= {'target':target,'format':'json'}
    if addn_params:
        params.update(addn_params)
    url='{0}/render/?{1}'.format(graphite_host,urlencode(params))
    log.debug("url:"+url)
    #return requests.get(url).json()
    return requests.get(url,timeout=5).json()

@app.route('/')
#@crossdomain(origin='*')
def hello_world():
    return open('static/snickers.html').read()

@app.route('/api/sensors')
def get_all_sensors():
    url="{0}/metrics/find/?query={1}&format=treejson".format(graphite_host,sensor_namespace).format('*')

    return json.dumps([ int(e['id'].split(".")[-1]) \
            for e in requests.get(url,timeout=5).json() ])

def sensor_to_graphite(sensor):
    import socket
    data =""
    now=datetime.now()
    sock = socket.socket()
    offset=int(point_value/2)
    log.debug("beginning to build sensor data")
    # create array for each second the sensor is 'alive'
    for i in range(point_value):
        ts=(now+timedelta(seconds=i-offset)).timestamp()
        data+="sensors.motion.id.%d 1 %d\n"%(sensor,ts)
    sock.connect((CARBON_HOST, CARBON_PORT))
    #log.debug(data)
    sock.sendall(data.encode())
    sock.close()
    return


@app.route('/api/sensors/<int:sensor>/activity')
def add_sensor_data(sensor):
    nowdate=datetime.now()
    timeout=timedelta(seconds=4)
    try:
        lasttime = datetime.fromtimestamp( get_last_sensor_data(sensor) )
        log.debug("lasttime: %s"%lasttime)
        log.debug("timeout : %s"%timeout)
        log.debug("nowdate : %s"%nowdate)
        if lasttime + timeout > nowdate:
            log.debug("ignoring duplicate activity of %d"%sensor)
            return json.dumps({'warn':'ignoring duplicate activity'})
        log.debug("not ignoring sensor %d" %sensor)
        log.debug("sending to graphite")
        try:
            sensor_to_graphite(sensor)
        except Exception as e:
            log.error(e)

        log.debug("publishing to chat")
        r.publish('chat',sensor)
        return json.dumps(True)

    except:
        return


@app.route('/api/time')
def current_time():
    return json.dumps(float(time()))


def get_last_sensor_data(sensor):
    last=0
    try:
        for data in reversed(data_from_graphite(sensor_namespace.format(sensor))[0]["datapoints"]):
            val=data[0]
            ts=data[1]
            if val: 
                last=ts
                break
    except: pass
    return float(last)

@app.route('/api/sensors/<int:sensor>/last')
def get_last(sensor):
    return json.dumps(get_last_sensor_data(sensor))


@app.route('/api/sensors/<int:sensor>/all')
def get_all_sensor_data(sensor):
    return "not implemented"
    q=data_from_graphite(sensor_namespace.format(sensor))
    #q=r.lrange(sensor_namespace.format(sensor),0,-1)
    return json.dumps([ float(i.decode()) for i in q ])


# def event_stream(delta):
#     # delta must be datetime.timedelta
#     import time
#     while True:
#         data =[]
#         for key in r.keys(sensor_namespace.format("*")):
#             ts = datetime.fromtimestamp(float(r.lrange(key,-1,-1)[0] ))
#             if ts + delta > datetime.now():
#                 data.append(int(key.decode().split(".")[-1]))
# 
#         yield "data: %s\n\n" %json.dumps(data)
#         time.sleep(5)
# 
# @app.route('/api/subscribe/10s')
# def stream1():
#     return Response(event_stream(timedelta(seconds=10)),
#                           mimetype="text/event-stream")
# @app.route('/api/subscribe/1m')
# def stream2():
#     return Response(event_stream(timedelta(minutes=1)),
#                           mimetype="text/event-stream")
# @app.route('/api/subscribe/10m')
# def stream3():
#     return Response(event_stream(timedelta(minutes=10)),
#                           mimetype="text/event-stream")

def activity_stream():
    pubsub = r.pubsub()
    pubsub.subscribe('chat')
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        if message['type'] == 'subscribe':
            print("connected subscribers: %d"%message['data'])
        else:
            print(message)
            yield 'data: %d\n\n' % int(message['data'].decode())

@app.route('/api/subscribe/live')
def livestream():
    return Response(activity_stream(),
                          mimetype="text/event-stream")

def relevant_sensors():
    return "not implemented"
    return [k.decode() for k in r.keys(rooms_namespace.format('*'))]

def sensor_mapping():
    return simple_sensor_mapping
    """
    ret = {}
    for key in relevant_sensors():
        ret[key.split('.')[-1]] = int(r.get(key).decode())
    return ret
    """

@app.route('/api/rooms')
def get_sensor_mapping():
    return json.dumps(sensor_mapping())

@app.route('/api/rooms/<name>/<int:id>')
def set_sensor(name,id):
    return "not implemented"
    import re
    name = re.sub('[^0-0a-zA-Z]','',name)
    return json.dumps(r.set(rooms_namespace.format(name),str(id)))

def shack_open(time):
    return True

def total_seconds(sensor,begin,end):
    #q=r.lrange(sensor_namespace.format(sensor),0,-1)
    q=data_from_graphite(sensor_namespace.format(sensor),
            {'from':begin.strftime("%H:%M_%Y%m%d"),'until':end.strftime("%H:%M_%Y%m%d")})

    total_time= end - begin
    total_secs = 0
    try:
        first_entry=q[0]
    except:
        return 0

    try:
        resolution = first_entry['datapoints'][1][1] - \
            first_entry['datapoints'][0][1]
    except:
        raise Exception("not enough data points returned")

    for value,timestamp in first_entry['datapoints']:
        e = datetime.fromtimestamp(timestamp)
        # only count if value is not None and the shack is open
        if shack_open(e) and value:
            # add as the seconds between the last and the current point
            total_secs +=resolution
    return total_secs


@app.route('/api/stats/<int:sensor>/total/day')
def total_stats(sensor):
    end=datetime.now()
    begin=end -timedelta(hours=24)
    return json.dumps(total_seconds(sensor,begin,end))

@app.route('/api/stats/<int:sensor>/total')
def total_everyday_stats(sensor):
    end=datetime.now()
    #begin=datetime.fromtimestamp(0)
    begin=end-timedelta(days=160)
    return json.dumps(total_seconds(sensor,begin,end))
    return total_seconds(sensor,
            datetime.now()-timedelta(hours=24),
            datetime.now())

@app.route('/api/stats')
def total():
    ret = {}
    end=datetime.now()
    #begin=datetime.fromtimestamp(0)
    begin=end-timedelta(days=160)
    total_secs=0
    for name,ident in sensor_mapping().items():
        secs = int(total_seconds(ident,begin,end))
        total_secs +=secs
        ret[ident] = {"name": name, "seconds": secs}
    print(ret)
    for ident,val in ret.items():
        ret[ident]['percent'] = float(ret[ident]['seconds'] /total_secs) * 100
    return json.dumps(ret)
    #return json.dumps({ "2037282": {"name":"lounge","seconds": 1234, "percent":81.3},"9846210": {"name":"kueche","seconds": 100, "percent":18.7} })

@app.route('/api/temperature')
def get_temperature():
    try:
        c = data_from_graphite(temperature_target)
        dp = c[0]['datapoints']
        for temperature,ts in reversed(dp):
            if temperature: 
                return json.dumps([temperature,ts])
    except:
        return json.dumps(['No Data',0])
if __name__ == '__main__':
    app.debug =True
    app.run(host='0.0.0.0',port=8888,threaded=True)

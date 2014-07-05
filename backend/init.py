#!/usr/bin/python

from flask import Flask,Response
from time import time
from datetime import datetime,timedelta
import json
app = Flask(__name__)
import redis
redis_host='shackles.shack'
redis_port=6379
redis_db=0
sensor_namespace='sensors.motion.{}'
timeout=timedelta(seconds=40)
point_value=timedelta(seconds=50)

r = redis.StrictRedis(host=redis_host, port=redis_port , db=redis_db)

@app.route('/')
def hello_world():
    return 'try:<br/>/api/sensors<br/>'

@app.route('/api/sensors')
def get_all_sensors():
    q=r.keys(sensor_namespace.format("*"))
    return json.dumps([ int(i.decode().split(".")[-1]) for i in q ])

@app.route('/api/sensors/<int:sensor>/activity')
def add_sensor_data(sensor):
    nowdate= datetime.now()
    timeout=timedelta(seconds=4)
    try:
        lasttime=datetime.fromtimestamp(float(r.lrange(sensor_namespace.format(sensor),-1,-1)[0]))
    except:
        lasttime=datetime.fromtimestamp(0)
    if nowdate > lasttime + timeout:
        r.publish('chat',sensor)
        return json.dumps(int(r.rpush(sensor_namespace.format(sensor),time())))
    else:
        #print("ignoring activity,timeout not reached")
        return json.dumps(False)
@app.route('/api/time')
def current_time():
    return json.dumps(float(time()))

@app.route('/api/sensors/<int:sensor>/last')
def get_last_sensor_data(sensor):
    q=r.lrange(sensor_namespace.format(sensor),-1,-1)[0]
    return json.dumps(float(q.decode()))


@app.route('/api/sensors/<int:sensor>/all')
def get_all_sensor_data(sensor):
    q=r.lrange(sensor_namespace.format(sensor),0,-1)
    return json.dumps([ float(i.decode()) for i in q ])

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
    

def event_stream(delta):
    # delta must be datetime.timedelta
    import time
    while True:
        data =[]
        for key in r.keys(sensor_namespace.format("*")):
            ts = datetime.fromtimestamp(float(r.lrange(key,-1,-1)[0] ))
            if ts + delta > datetime.now():
                data.append(int(key.decode().split(".")[-1]))

        yield "data: %s\n\n" %json.dumps(data)
        time.sleep(5)

@app.route('/api/subscribe/10s')
def stream1():
    return Response(event_stream(timedelta(seconds=10)),
                          mimetype="text/event-stream")
@app.route('/api/subscribe/1m')
def stream2():
    return Response(event_stream(timedelta(minutes=1)),
                          mimetype="text/event-stream")
@app.route('/api/subscribe/10m')
def stream3():
    return Response(event_stream(timedelta(minutes=10)),
                          mimetype="text/event-stream")
@app.route('/api/subscribe/live')
def livestream():
    return Response(activity_stream(),
                          mimetype="text/event-stream")

def shack_open(time):
    return True

def total_seconds(sensor,begin,end):
    q=r.lrange(sensor_namespace.format(sensor),0,-1)
    total_time= end - begin
    print ("balls")
    total_points=0
    for entry in q:
        e = datetime.fromtimestamp(float(entry))
        if begin < e < end and shack_open(e):
            total_points +=1
    return total_points * point_value.seconds


@app.route('/api/stats/<int:sensor>/total/day')
def total_stats(sensor):
    print("aidsballs")
    end=datetime.now()
    print(end)
    begin=end -timedelta(hours=24)
    print(begin)
    return json.dumps(total_seconds(sensor,begin,end))
    #return total_seconds(sensor,
            #datetime.now()-timedelta(hours=24),
            #datetime.now())


if __name__ == '__main__':
    app.debug =True
    app.run(host='0.0.0.0',port=8888,threaded=True)

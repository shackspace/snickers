#!/usr/bin/python

from flask import Flask,Response
from datetime import datetime,timedelta
import json
app = Flask(__name__)
import redis
redis_host='shackles.shack'
redis_port=6379
redis_db=0
sensor_namespace='sensors.motion.{}'

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
    from time import time
    r.publish('chat',sensor)
    return json.dumps(int(r.rpush(sensor_namespace.format(sensor),time())))

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
if __name__ == '__main__':
    app.debug =True
    app.run(host='0.0.0.0',port=8888,threaded=True)

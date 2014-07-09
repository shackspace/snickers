
# list sensors

    curl http://localhost/api/sensors
    
    # return json array of sensor ids
    > [1,323432,45452]


# get last sensor activity

    curl http://localhost/api/sensors/<id>/last

    # return timestamp 
    > 123456.12345

# get all sensor activity

    curl http://localhost/api/sensors/<id>/all

    # return all timestamps
    > [123456.12345,123432.12345]

# post new activity

    curl http://localhost/api/sensors/<id>/activity

    # return number of all timestamps after adding


#  Get the server time

    curl http://localhost/api/time

    > 123456.12345

# get the total seconds the sensor was active in the last 24 hours

    curl http://localhost/api/stats/<sensor-id>/total/day

    > 750
    
# get the total seconds the sensor was active (all time) 

    curl http://localhost/api/stats/<sensor-id>/total/everytime

    > 75340

# get total seconds for the sensor

    curl http://localhost/api/stats/<sensor-id>/total

    > 1600

# subscribe live

  curl http://localhost/api/subscribe/live

  > data: 1234

# get room-id mapping

  curl http://localhost/api/rooms

  > {'lounge':1234,'kueche':4321}

# update room mapping

  curl http://localhost/api/rooms/<name>/<ident>

  > OK

# get all the stats

  curl http://localhost/api/stats

  > {"2037282": {"seconds": 79300, "name": "lounge", "percent": 51.93189259986902}, "9846210": {"seconds": 73400, "name": "kueche", "percent": 48.06810740013098}
# Subject to change

## subscribe to sensor activity in the last 10s/1m/10m

  curl http://localhost/api/subscribe/{10s,1m,10m}

  > data: [1234]
  >
  > data: [1234,4321]


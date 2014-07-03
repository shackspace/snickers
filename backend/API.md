
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


# Subject to change

## subscribe to sensor activity in the last 10s/1m/10m

  curl http://localhost/api/subscribe/{10s,1m,10m}

  > data: [1234]
  >
  > data: [1234,4321]


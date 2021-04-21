#! /bin/bash -e
docker run \
    --rm \
    -t \
    -e INFLUXDB_V2_TOKEN \
    -e INFLUXDB_V2_URL \
    -e INFLUXDB_V2_ORG \
    -e INFLUXDB_V2_SSL_CA_CERT \
    -e JEMENA_USERNAME \
    -e JEMENA_PASSWORD \
    -e INFLUX_BUCKET \
    cgspeck/jemena-to-influx:latest


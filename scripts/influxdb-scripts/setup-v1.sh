#!/bin/bash
set -e

influx v1 auth create \
  --username ${V1_AUTH_USERNAME} \
  --password ${V1_AUTH_PASSWORD} \
  --write-bucket ${DOCKER_INFLUXDB_INIT_BUCKET_ID} \
  --org ${INFLUXDB_ORG} \
  --token ${INFLUXDB_TOKEN}
#!/bin/bash

APP_ADDR=localhost:5000
API_CALL=$1

if [ -z "$API_CALL" ]; then
  echo "Usage: $0 <api-call>"
  echo "read the README.md file for more information"
  exit 1
fi

curl -k -X POST -H "Content-Type: application/json" -d @$API_CALL.json https://$APP_ADDR/api/v1/$API_CALL
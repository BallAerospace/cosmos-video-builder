#!/usr/bin/env sh

set -e

usage() {
  echo "Usage: $1 [start, stop, build]" >&2
  echo "*  start: run the docker containers for the local video builder" >&2
  echo "*  stop: stop the running docker containers for the local video builder" >&2
  echo "*  build: build the containers for the local video builder" >&2
  exit 1
}

if [ "$#" -eq 0 ]; then
  usage $0
fi

case $1 in
  start )
    docker-compose -f compose.yaml build
    docker-compose -f compose.yaml up -d
    ;;
  stop )
    docker-compose -f compose.yaml down
    ;;
  build )
    docker-compose -f compose.yaml build
    ;;
  * )
    usage $0
    ;;
esac

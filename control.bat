@echo off
setlocal ENABLEDELAYEDEXPANSION

if "%1" == "" (
  GOTO usage
)
if "%1" == "start" (
  GOTO startup
)
if "%1" == "stop" (
  GOTO stop
)
if "%1" == "build" (
  GOTO build
)

GOTO usage

:startup
  docker-compose -f compose.yaml build
  docker-compose -f compose.yaml up -d
  @echo off
GOTO :EOF

:stop
  docker-compose -f compose.yaml down
  @echo off
GOTO :EOF

:build
  docker-compose -f compose.yaml build
  @echo off
GOTO :EOF

:usage
  @echo Usage: %0 [start, stop, build] 1>&2
  @echo *  start: run the docker containers for the local video builder 1>&2
  @echo *  stop: stop the running docker containers for the local video builder 1>&2
  @echo *  build: build the containers for the local video builder 1>&2

@echo on

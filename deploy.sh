#!/bin/bash
heroku container:login
heroku container:push    -a ghostsystem-api web
heroku container:release -a ghostsystem-api web
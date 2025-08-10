#!/bin/bash

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    if ! command -v docker-compose &> /dev/null; then
        echo "Error: Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    else
        docker-compose up -d --build
        exit $?
    fi
fi

docker compose up -d --build


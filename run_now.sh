#!/bin/bash

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

if docker compose version &> /dev/null; then
    echo "Pulling latest image for specific services..."
    docker compose pull fastapi
    echo "Starting services with Docker Compose, using registry ghcr.io/tech-dex/fastapi-infra-kit:latest"
    docker compose up -d --build
else
    if ! command -v docker-compose &> /dev/null; then
        echo "Error: Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    else
        echo "Pulling latest image for specific services..."
        docker-compose pull fastapi
        echo "Starting services with Docker Compose, using registry ghcr.io/tech-dex/fastapi-infra-kit:latest"
        docker-compose up -d --build
        exit $?
    fi
fi

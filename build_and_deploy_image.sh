#!/bin/bash

image_name="meshtastic_mesh_visualizer"

# Argument check (Accepts branch name as an argument, defaults to main)
branch=${1:-main}

function print_section() {
    printf "\n\n\n***************************************************\n"
    printf "$1\n"
    printf "***************************************************\n\n\n"
}

# Stop and remove the Docker container
print_section "Stopping and removing the Docker container..."
docker compose down
docker container ls -a | grep $image_name | awk '{print $1}' | xargs docker container rm

# Build the image using the dedicated build script
print_section "Building the Docker image..."
./build_image.sh $branch

# Run Docker Compose in detached mode
print_section "Running Docker Compose in detached mode..."
docker compose up -d

# Run docker logs -f
print_section "Running docker logs -f..."
docker logs -f $image_name
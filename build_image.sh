#!/bin/bash

image_name="meshtastic_mesh_visualizer"

# Argument check (Accepts branch name as an argument, defaults to main)
branch=${1:-main}

function print_section() {
    printf "\n\n\n***************************************************\n"
    printf "$1\n"
    printf "***************************************************\n\n\n"
}

# Checkout to the specified branch
print_section "Checking out to the specified branch..."
git fetch
git checkout $branch

# Pull the latest changes from the repository
print_section "Pulling the latest changes from the repository..."
git pull

# Build the Docker image
print_section "Building the Docker image..."
docker build -t $image_name .
docker image ls | grep $image_name

print_section "Image build complete!"
echo "Image name: $image_name"
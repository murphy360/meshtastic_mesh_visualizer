#!/bin/bash

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
readonly IMAGE_NAME="meshtastic_mesh_visualizer"
readonly CONTAINER_NAME="meshtastic_mesh_visualizer"
readonly COMPOSE_FILE="docker-compose.yaml"
readonly DEFAULT_BRANCH="main"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Argument handling
branch=${1:-$DEFAULT_BRANCH}

function print_section() {
    echo -e "\n${BLUE}=================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

function validate_environment() {
    print_section "Validating Environment"
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
    fi
    
    # Check if docker compose is available
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
    fi
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Docker Compose file '$COMPOSE_FILE' not found"
    fi
    
    # Check if build script exists
    if [[ ! -f "build_image.sh" ]]; then
        print_error "build_image.sh script not found"
    fi
    
    print_success "Environment validation passed"
}

function stop_existing_services() {
    print_section "Stopping Existing Services"
    
    # Stop docker compose services
    if docker compose ps -q 2>/dev/null | grep -q .; then
        echo "Stopping Docker Compose services..."
        docker compose down || print_warning "Failed to stop some compose services"
        print_success "Docker Compose services stopped"
    else
        print_success "No running compose services found"
    fi
    
    # Find and stop any containers with the same name
    local existing_containers=$(docker ps -a --filter "name=$CONTAINER_NAME" -q)
    if [[ -n "$existing_containers" ]]; then
        echo "Stopping and removing existing containers..."
        docker stop $existing_containers || print_warning "Failed to stop some containers"
        docker rm $existing_containers || print_warning "Failed to remove some containers"
        print_success "Existing containers cleaned up"
    else
        print_success "No existing containers to clean up"
    fi
}

function build_image() {
    print_section "Building Docker Image"
    
    # Make build script executable
    chmod +x build_image.sh
    
    # Run the build script
    if ./build_image.sh "$branch"; then
        print_success "Image build completed successfully"
    else
        print_error "Image build failed"
    fi
}

function deploy_services() {
    print_section "Deploying Services"
    
    # Start services with docker compose
    echo "Starting services with Docker Compose..."
    if docker compose up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
    fi
    
    # Wait a moment for services to initialize
    echo "Waiting for services to initialize..."
    sleep 5
    
    # Check service status
    echo -e "\nService status:"
    docker compose ps
}

function show_deployment_info() {
    print_section "Deployment Information"
    
    # Show running containers
    echo "Running containers:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Show service logs (last 20 lines)
    echo -e "\nRecent logs:"
    docker compose logs --tail=20
    
    # Show useful commands
    echo -e "\n${BLUE}Useful commands:${NC}"
    echo "  • View logs: docker compose logs -f"
    echo "  • Stop services: docker compose down"
    echo "  • Restart services: docker compose restart"
    echo "  • Access app: http://localhost:5000"
    echo "  • Check status: docker compose ps"
}

function follow_logs() {
    print_section "Following Application Logs"
    
    echo -e "${YELLOW}Press Ctrl+C to stop following logs${NC}\n"
    
    # Follow logs for the main service
    if docker compose logs -f mesh-visualizer; then
        print_success "Log following stopped"
    else
        print_warning "Failed to follow logs, service may not be running"
    fi
}

function main() {
    print_section "Meshtastic Mesh Visualizer - Build and Deploy"
    echo "Branch: $branch"
    echo "Image: $IMAGE_NAME"
    echo "Container: $CONTAINER_NAME"
    echo "Compose File: $COMPOSE_FILE"
    
    validate_environment
    stop_existing_services
    build_image
    deploy_services
    show_deployment_info
    
    print_section "Deployment Complete!"
    echo -e "${GREEN}Services deployed successfully${NC}"
    
    # Ask user if they want to follow logs
    echo -e "\n${BLUE}Would you like to follow the application logs? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        follow_logs
    else
        echo -e "${BLUE}Deployment finished. Use 'docker compose logs -f' to view logs.${NC}"
    fi
}

# Run main function
main "$@"
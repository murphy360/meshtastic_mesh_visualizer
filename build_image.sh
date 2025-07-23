#!/bin/bash

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
readonly IMAGE_NAME="meshtastic_mesh_visualizer"
readonly DOCKERFILE="Dockerfile"
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
    
    # Check if Dockerfile exists
    if [[ ! -f "$DOCKERFILE" ]]; then
        print_error "Dockerfile not found in current directory"
    fi
    
    # Check if requirements.txt exists
    if [[ ! -f "requirements.txt" ]]; then
        print_error "requirements.txt not found"
    fi
    
    # Check if src directory exists
    if [[ ! -d "src" ]]; then
        print_error "src directory not found"
    fi
    
    print_success "Environment validation passed"
}

function update_repository() {
    print_section "Updating Repository to Branch: $branch"
    
    # Fetch latest changes
    if ! git fetch; then
        print_error "Failed to fetch from remote repository"
    fi
    
    # Check if branch exists
    if ! git show-ref --verify --quiet refs/heads/"$branch" && \
       ! git show-ref --verify --quiet refs/remotes/origin/"$branch"; then
        print_error "Branch '$branch' does not exist"
    fi
    
    # Checkout to specified branch
    if ! git checkout "$branch"; then
        print_error "Failed to checkout branch '$branch'"
    fi
    
    # Pull latest changes
    if ! git pull origin "$branch"; then
        print_warning "Failed to pull latest changes, continuing with current state"
    fi
    
    local commit_hash=$(git rev-parse --short HEAD)
    print_success "Repository updated to branch '$branch' (commit: $commit_hash)"
}

function build_image() {
    print_section "Building $IMAGE_NAME Docker Image"

    local build_args=(
        "--tag" "$IMAGE_NAME"
        "--label" "branch=$branch"
        "--label" "build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        "--label" "git-commit=$(git rev-parse HEAD)"
        "."
    )
    
    echo "Building with command: docker build ${build_args[*]}"
    
    if docker build "${build_args[@]}"; then
        print_success "Docker image built successfully"
    else
        print_error "Docker build failed"
    fi
}

function show_image_info() {
    print_section "Image Information"
    
    # Show image details with error handling
    echo "Image details:"
    if docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null; then
        echo ""
    else
        print_warning "Failed to show image details"
    fi
    
    # Show basic image info as fallback
    echo "Basic image info:"
    if docker images "$IMAGE_NAME" 2>/dev/null; then
        echo ""
    else
        print_warning "Failed to show basic image info"
    fi
    
    # Show image labels with error handling
    echo "Image labels:"
    if docker inspect "$IMAGE_NAME" --format '{{range $k, $v := .Config.Labels}}{{if ne $k "com.docker.compose.config-hash"}}{{$k}}: {{$v}}{{"\n"}}{{end}}{{end}}' 2>/dev/null; then
        echo ""
    else
        print_warning "Failed to show image labels"
    fi
    
    print_success "Image information displayed"
}

function cleanup_old_images() {
    print_section "Cleaning Up Old Images"
    
    # Remove dangling images
    local dangling_images=$(docker images -f "dangling=true" -q)
    if [[ -n "$dangling_images" ]]; then
        echo "Removing dangling images..."
        docker rmi $dangling_images || print_warning "Failed to remove some dangling images"
        print_success "Dangling images removed"
    else
        print_success "No dangling images to remove"
    fi
}

function main() {
    print_section "Meshtastic Mesh Visualizer - Docker Build"
    echo "Branch: $branch"
    echo "Image: $IMAGE_NAME"
    echo "Dockerfile: $DOCKERFILE"
    
    validate_environment
    update_repository
    cleanup_old_images
    build_image
    show_image_info
    
    print_section "Build Complete!"
    echo -e "${GREEN}Image '$IMAGE_NAME' built successfully from branch '$branch'${NC}"
    echo -e "${BLUE}Next steps:${NC}"
    echo "  • Test the image: docker run --rm -p 5000:5000 $IMAGE_NAME"
    echo "  • Deploy with compose: docker compose up -d"
    echo "  • View logs: docker logs $IMAGE_NAME"
}

# Run main function
main "$@"
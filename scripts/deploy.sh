#!/bin/bash
# ScienceRAG Deployment Script
# Handles deployment to different environments

set -e

# Configuration
PROJECT_NAME="sciencerag"
ENVIRONMENT=${1:-"production"}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Please create it with required environment variables."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images for ${ENVIRONMENT}..."

    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi

    # Build with no cache for production
    if [ "$ENVIRONMENT" = "production" ]; then
        docker compose -f "$COMPOSE_FILE" build --no-cache
    else
        docker compose -f "$COMPOSE_FILE" build
    fi

    log_success "Docker images built successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    docker compose -f "$COMPOSE_FILE" exec -T postgres sh -c '
        for i in {1..30}; do
            if pg_isready -U $POSTGRES_USER -d $POSTGRES_DB; then
                echo "Database is ready"
                exit 0
            fi
            echo "Waiting for database... ($i/30)"
            sleep 2
        done
        echo "Database failed to start"
        exit 1
    '

    # Run migrations
    docker compose -f "$COMPOSE_FILE" exec -T backend sh -c '
        cd /app && alembic upgrade head
    '

    log_success "Database migrations completed"
}

# Start services
start_services() {
    log_info "Starting services..."

    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi

    # Start services
    docker compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."

    # Check backend health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Backend failed to become healthy"
            exit 1
        fi
        echo "Waiting for backend... ($i/30)"
        sleep 5
    done

    # Check frontend health
    for i in {1..20}; do
        if curl -f http://localhost:3000 &> /dev/null; then
            log_success "Frontend is healthy"
            break
        fi
        if [ $i -eq 20 ]; then
            log_warning "Frontend health check failed, but continuing..."
            break
        fi
        echo "Waiting for frontend... ($i/20)"
        sleep 3
    done

    log_success "All services started successfully"
}

# Run health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."

    # Check API endpoints
    endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/docs"
        "http://localhost:3000"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -f "$endpoint" &> /dev/null; then
            log_success "✓ $endpoint is accessible"
        else
            log_error "✗ $endpoint is not accessible"
            return 1
        fi
    done

    # Check database connectivity
    if docker compose -f docker-compose.yml exec -T backend python -c "
import asyncio
from app.database import check_db_connection
result = asyncio.run(check_db_connection())
exit(0 if result else 1)
" 2>/dev/null; then
        log_success "✓ Database connectivity OK"
    else
        log_error "✗ Database connectivity failed"
        return 1
    fi

    log_success "All health checks passed"
}

# Clean up old resources
cleanup() {
    log_info "Cleaning up old Docker resources..."

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    # Remove unused networks
    docker network prune -f

    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment to ${ENVIRONMENT} environment..."

    check_prerequisites
    build_images
    start_services
    run_migrations
    run_health_checks

    log_success "🎉 Deployment to ${ENVIRONMENT} completed successfully!"
    log_info ""
    log_info "Application URLs:"
    log_info "  Frontend: http://localhost:3000"
    log_info "  Backend API: http://localhost:8000"
    log_info "  API Docs: http://localhost:8000/docs"
    log_info ""
    log_info "To view logs: docker compose logs -f"
    log_info "To stop services: docker compose down"
}

# Rollback function
rollback() {
    log_warning "Starting rollback..."

    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi

    # Stop services
    docker compose -f "$COMPOSE_FILE" down

    # Start previous version if available
    # This would need to be implemented based on your versioning strategy

    log_warning "Rollback completed. Manual intervention may be required."
}

# Show usage
usage() {
    echo "ScienceRAG Deployment Script"
    echo ""
    echo "Usage: $0 [environment] [command]"
    echo ""
    echo "Environments:"
    echo "  development  Deploy to development environment (default)"
    echo "  production   Deploy to production environment"
    echo ""
    echo "Commands:"
    echo "  deploy       Full deployment (default)"
    echo "  build        Build Docker images only"
    echo "  start        Start services only"
    echo "  migrate      Run migrations only"
    echo "  health       Run health checks only"
    echo "  cleanup      Clean up Docker resources"
    echo "  rollback     Rollback deployment"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to development"
    echo "  $0 production        # Deploy to production"
    echo "  $0 development build # Build development images only"
}

# Parse command line arguments
COMMAND=${2:-"deploy"}

case "$COMMAND" in
    "deploy")
        deploy
        ;;
    "build")
        check_prerequisites
        build_images
        ;;
    "start")
        start_services
        ;;
    "migrate")
        run_migrations
        ;;
    "health")
        run_health_checks
        ;;
    "cleanup")
        cleanup
        ;;
    "rollback")
        rollback
        ;;
    *)
        usage
        exit 1
        ;;
esac
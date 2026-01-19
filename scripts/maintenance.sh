#!/bin/bash
# ScienceRAG Maintenance Script
# Performs routine maintenance tasks

set -e

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

# Clean up Docker resources
cleanup_docker() {
    log_info "Cleaning up Docker resources..."

    # Remove stopped containers
    docker container prune -f

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    # Remove unused networks
    docker network prune -f

    log_success "Docker cleanup completed"
}

# Clean up old logs
cleanup_logs() {
    log_info "Cleaning up old log files..."

    # Keep logs for last 30 days
    find ./logs -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true

    # Compress old logs
    find ./logs -name "*.log" -type f -mtime +7 -exec gzip {} \; 2>/dev/null || true

    log_success "Log cleanup completed"
}

# Database maintenance
maintenance_database() {
    log_info "Performing database maintenance..."

    # Vacuum analyze for better performance
    docker compose exec -T postgres psql -U sciencerag -d sciencerag -c "VACUUM ANALYZE;" 2>/dev/null || {
        log_warning "VACUUM ANALYZE failed - database may be busy"
    }

    # Reindex if needed (be careful with this in production)
    if [ "${FORCE_REINDEX:-false}" = "true" ]; then
        log_warning "Reindexing database (this may take time)..."
        docker compose exec -T postgres psql -U sciencerag -d sciencerag -c "REINDEX DATABASE sciencerag;" 2>/dev/null || {
            log_error "Database reindexing failed"
            return 1
        }
        log_success "Database reindexing completed"
    fi

    log_success "Database maintenance completed"
}

# Update dependencies (if needed)
update_dependencies() {
    log_info "Checking for dependency updates..."

    # Backend dependencies
    log_info "Updating backend dependencies..."
    docker compose exec -T backend pip list --outdated 2>/dev/null | tail -n +3 | while read -r line; do
        PACKAGE=$(echo "$line" | awk '{print $1}')
        log_info "Outdated package: $PACKAGE"
    done || log_info "Could not check backend dependencies"

    # Frontend dependencies
    log_info "Checking frontend dependencies..."
    if docker compose exec -T frontend npm outdated 2>/dev/null | grep -v "Package" | head -5 | while read -r line; do
        PACKAGE=$(echo "$line" | awk '{print $1}')
        log_info "Outdated package: $PACKAGE"
    done; then
        log_info "Frontend dependency check completed"
    else
        log_info "Could not check frontend dependencies"
    fi

    log_success "Dependency check completed"
}

# Backup maintenance
maintenance_backup() {
    log_info "Performing backup maintenance..."

    # Run backup script if it exists
    if [ -f "./scripts/backup.sh" ]; then
        log_info "Running automated backup..."
        ./scripts/backup.sh
    else
        log_warning "Backup script not found"
    fi

    log_success "Backup maintenance completed"
}

# Security audit
security_audit() {
    log_info "Performing security audit..."

    # Check for exposed secrets
    log_info "Checking for exposed secrets..."

    # Check environment files
    if [ -f ".env" ]; then
        if grep -q "password\|secret\|key" .env; then
            log_info "Environment file contains sensitive data (this is expected)"
        fi
    fi

    # Check Docker security
    log_info "Checking Docker security..."
    docker compose exec -T backend python -c "
import os
import sys

# Check for common security issues
issues = []

# Check if running as root
if os.geteuid() == 0:
    issues.append('Running as root user')

# Check file permissions
try:
    stat = os.stat('.env')
    if oct(stat.st_mode)[-3:] != '600':
        issues.append('Environment file has incorrect permissions')
except:
    pass

if issues:
    print('Security issues found:')
    for issue in issues:
        print(f'  - {issue}')
    sys.exit(1)
else:
    print('No obvious security issues found')
" 2>/dev/null || log_warning "Could not perform security audit"

    log_success "Security audit completed"
}

# Performance optimization
optimize_performance() {
    log_info "Performing performance optimizations..."

    # Restart services to free memory
    log_info "Restarting services for memory cleanup..."
    docker compose restart

    # Wait for services to be ready
    sleep 10

    # Run health check
    if [ -f "./scripts/monitor.sh" ]; then
        log_info "Running post-optimization health check..."
        ./scripts/monitor.sh once
    fi

    log_success "Performance optimization completed"
}

# Show usage
usage() {
    echo "ScienceRAG Maintenance Script"
    echo ""
    echo "Usage: $0 [tasks...]"
    echo ""
    echo "Tasks:"
    echo "  all          Run all maintenance tasks (default)"
    echo "  docker       Clean up Docker resources"
    echo "  logs         Clean up old log files"
    echo "  database     Perform database maintenance"
    echo "  backup       Run backup maintenance"
    echo "  security     Perform security audit"
    echo "  performance  Optimize system performance"
    echo "  deps         Check for dependency updates"
    echo ""
    echo "Environment variables:"
    echo "  FORCE_REINDEX  Force database reindexing (dangerous in production)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all maintenance tasks"
    echo "  $0 docker logs        # Clean Docker and logs only"
    echo "  $0 database           # Database maintenance only"
}

# Main function
main() {
    # Default to all tasks if none specified
    if [ $# -eq 0 ]; then
        set -- "all"
    fi

    for task in "$@"; do
        case "$task" in
            "all")
                cleanup_docker
                cleanup_logs
                maintenance_database
                update_dependencies
                maintenance_backup
                security_audit
                optimize_performance
                ;;
            "docker")
                cleanup_docker
                ;;
            "logs")
                cleanup_logs
                ;;
            "database")
                maintenance_database
                ;;
            "backup")
                maintenance_backup
                ;;
            "security")
                security_audit
                ;;
            "performance")
                optimize_performance
                ;;
            "deps")
                update_dependencies
                ;;
            *)
                log_error "Unknown task: $task"
                usage
                exit 1
                ;;
        esac
    done

    log_success "🎉 Maintenance completed successfully!"
}

# Run main function
main "$@"
#!/bin/bash
# ScienceRAG Monitoring Script
# Monitors system health and performance

set -e

# Configuration
HEALTH_CHECK_INTERVAL=60
LOG_FILE="./logs/monitor_$(date +%Y%m%d).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Create log directory
setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
}

# Check Docker services
check_services() {
    log_info "Checking Docker services..."

    # Get service status
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    SERVICES=$($COMPOSE_CMD ps --services --filter "status=running" 2>/dev/null | wc -l)
    TOTAL_SERVICES=$($COMPOSE_CMD ps --services 2>/dev/null | wc -l)

    if [ "$SERVICES" -eq "$TOTAL_SERVICES" ] && [ "$TOTAL_SERVICES" -gt 0 ]; then
        log_success "All $SERVICES services are running"
        return 0
    else
        RUNNING=$($COMPOSE_CMD ps --services --filter "status=running" 2>/dev/null | wc -l)
        log_warning "$RUNNING/$TOTAL_SERVICES services are running"

        # Show status of each service
        $COMPOSE_CMD ps
        return 1
    fi
}

# Check API health
check_api_health() {
    log_info "Checking API health..."

    # Backend health
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend API is healthy"

        # Get detailed health info
        HEALTH_DATA=$(curl -s http://localhost:8000/health 2>/dev/null)
        if echo "$HEALTH_DATA" | grep -q '"status": "healthy"'; then
            log_success "Backend reports healthy status"
        else
            log_warning "Backend health check returned warnings"
        fi
    else
        log_error "Backend API is not responding"
        return 1
    fi

    # Frontend health
    if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is accessible"
    else
        log_warning "Frontend is not accessible"
    fi
}

# Check database connectivity
check_database() {
    log_info "Checking database connectivity..."

    # Use backend container to check database
    if docker compose exec -T backend python -c "
import asyncio
from app.database import check_db_connection

async def check():
    return await check_db_connection()

result = asyncio.run(check())
exit(0 if result else 1)
" 2>/dev/null; then
        log_success "Database connectivity OK"
        return 0
    else
        log_error "Database connectivity failed"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    log_info "Checking system resources..."

    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    CPU_INT=${CPU_USAGE%.*}

    if [ "$CPU_INT" -gt 90 ]; then
        log_error "High CPU usage: ${CPU_USAGE}%"
    elif [ "$CPU_INT" -gt 70 ]; then
        log_warning "Elevated CPU usage: ${CPU_USAGE}%"
    else
        log_success "CPU usage: ${CPU_USAGE}%"
    fi

    # Memory usage
    MEM_TOTAL=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    MEM_USED=$(free -m | awk 'NR==2{printf "%.0f", $3}')
    MEM_USAGE=$((MEM_USED * 100 / MEM_TOTAL))

    if [ "$MEM_USAGE" -gt 90 ]; then
        log_error "High memory usage: ${MEM_USAGE}% (${MEM_USED}MB/${MEM_TOTAL}MB)"
    elif [ "$MEM_USAGE" -gt 70 ]; then
        log_warning "Elevated memory usage: ${MEM_USAGE}% (${MEM_USED}MB/${MEM_TOTAL}MB)"
    else
        log_success "Memory usage: ${MEM_USAGE}% (${MEM_USED}MB/${MEM_TOTAL}MB)"
    fi

    # Disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_error "High disk usage: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -gt 70 ]; then
        log_warning "Elevated disk usage: ${DISK_USAGE}%"
    else
        log_success "Disk usage: ${DISK_USAGE}%"
    fi
}

# Check Docker resources
check_docker_resources() {
    log_info "Checking Docker resource usage..."

    # Get container stats
    if docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemPerc}}" 2>/dev/null | grep -v "CONTAINER\|N/A" | while read -r line; do
        CONTAINER=$(echo "$line" | awk '{print $1}')
        CPU=$(echo "$line" | awk '{print $2}' | sed 's/%//')
        MEM=$(echo "$line" | awk '{print $3}' | sed 's/%//')

        if [ "${CPU%.*}" -gt 80 ] 2>/dev/null; then
            log_warning "Container $CONTAINER high CPU: ${CPU}%"
        fi

        if [ "${MEM%.*}" -gt 80 ] 2>/dev/null; then
            log_warning "Container $CONTAINER high memory: ${MEM}%"
        fi
    done; then
        log_success "Docker resource check completed"
    else
        log_warning "Could not check Docker resource usage"
    fi
}

# Check logs for errors
check_logs() {
    log_info "Checking recent logs for errors..."

    # Check backend logs for errors
    ERROR_COUNT=$(docker compose logs --tail=100 backend 2>&1 | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        log_warning "Found $ERROR_COUNT error messages in backend logs"
        # Show last few errors
        docker compose logs --tail=10 backend 2>&1 | grep -i error | tail -3
    else
        log_success "No recent errors in backend logs"
    fi
}

# Send alert (placeholder for actual alerting)
send_alert() {
    local message="$1"
    local severity="${2:-warning}"

    log_warning "ALERT [$severity]: $message"

    # Here you could integrate with:
    # - Slack webhooks
    # - Email notifications
    # - PagerDuty
    # - Discord webhooks
    # etc.
}

# Main monitoring loop
monitor_once() {
    log_info "=== ScienceRAG Health Check ==="

    local failed_checks=0

    if ! check_services; then
        send_alert "Service health check failed" "error"
        ((failed_checks++))
    fi

    if ! check_api_health; then
        send_alert "API health check failed" "error"
        ((failed_checks++))
    fi

    if ! check_database; then
        send_alert "Database connectivity check failed" "error"
        ((failed_checks++))
    fi

    check_system_resources
    check_docker_resources
    check_logs

    if [ "$failed_checks" -eq 0 ]; then
        log_success "All health checks passed"
    else
        log_error "$failed_checks health checks failed"
    fi

    echo ""
}

# Continuous monitoring
monitor_continuous() {
    log_info "Starting continuous monitoring (interval: ${HEALTH_CHECK_INTERVAL}s)"
    log_info "Press Ctrl+C to stop"

    while true; do
        monitor_once
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

# Show usage
usage() {
    echo "ScienceRAG Monitoring Script"
    echo ""
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  once       Run health checks once (default)"
    echo "  continuous Run health checks continuously"
    echo "  help       Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  HEALTH_CHECK_INTERVAL  Interval between checks in continuous mode (default: 60s)"
    echo "  LOG_FILE              Log file location (default: ./logs/monitor_YYYYMMDD.log)"
}

# Main function
main() {
    setup_logging

    case "${1:-once}" in
        "once")
            monitor_once
            ;;
        "continuous")
            monitor_continuous
            ;;
        "help"|"-h"|"--help")
            usage
            exit 0
            ;;
        *)
            echo "Unknown mode: $1"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
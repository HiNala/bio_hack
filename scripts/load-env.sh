#!/bin/bash
# Environment Configuration Loader
# Automatically loads the correct environment configuration

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

# Determine environment
detect_environment() {
    # Check command line argument first
    if [ -n "$1" ]; then
        ENVIRONMENT="$1"
    # Check NODE_ENV or RAILS_ENV or similar
    elif [ -n "$NODE_ENV" ]; then
        ENVIRONMENT="$NODE_ENV"
    elif [ -n "$RAILS_ENV" ]; then
        ENVIRONMENT="$RAILS_ENV"
    elif [ -n "$APP_ENV" ]; then
        ENVIRONMENT="$APP_ENV"
    # Check hostname patterns
    elif [[ "$(hostname)" == *"prod"* ]] || [[ "$(hostname)" == *"production"* ]]; then
        ENVIRONMENT="production"
    elif [[ "$(hostname)" == *"stag"* ]] || [[ "$(hostname)" == *"staging"* ]]; then
        ENVIRONMENT="staging"
    elif [[ "$(hostname)" == *"dev"* ]] || [[ "$(hostname)" == *"development"* ]]; then
        ENVIRONMENT="development"
    # Check for CI/CD indicators
    elif [ -n "$CI" ] || [ -n "$CONTINUOUS_INTEGRATION" ]; then
        ENVIRONMENT="ci"
    # Default to development
    else
        ENVIRONMENT="development"
    fi

    echo "$ENVIRONMENT"
}

# Load environment configuration
load_environment() {
    local env_file=".env.$ENVIRONMENT"

    if [ -f "$env_file" ]; then
        log_info "Loading environment configuration: $env_file"

        # Source the environment file
        set -a
        source "$env_file"
        set +a

        log_success "Environment configuration loaded from $env_file"
    elif [ -f ".env" ]; then
        log_warning "Environment-specific file not found, using default .env"
        set -a
        source ".env"
        set +a
    else
        log_error "No environment configuration found"
        log_info "Create .env or .env.$ENVIRONMENT file"
        exit 1
    fi
}

# Validate required environment variables
validate_environment() {
    local missing_vars=()

    # Check for required variables based on environment
    case "$ENVIRONMENT" in
        "production"|"staging")
            # Required for production/staging
            required_vars=(
                "OPENAI_API_KEY"
                "DATABASE_URL"
                "SECRET_KEY"
            )
            ;;
        "development")
            # Required for development (can use defaults)
            required_vars=(
                "OPENAI_API_KEY"
            )
            ;;
        *)
            required_vars=()
            ;;
    esac

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi

    log_success "Environment validation passed"
}

# Export environment information
export_environment_info() {
    log_info "Environment: $ENVIRONMENT"

    if [ "$VERBOSE" = "true" ]; then
        log_info "Active environment variables:"
        env | grep -E '^(APP_|DATABASE_|REDIS_|OPENAI_|ANTHROPIC_)' | sort
    fi
}

# Setup environment-specific configurations
setup_environment() {
    case "$ENVIRONMENT" in
        "development")
            export COMPOSE_FILE="docker-compose.yml:docker-compose.dev.yml"
            export NODE_ENV="development"
            export DEBUG="true"
            ;;
        "staging")
            export COMPOSE_FILE="docker-compose.yml:docker-compose.staging.yml"
            export NODE_ENV="production"
            export DEBUG="false"
            ;;
        "production")
            export COMPOSE_FILE="docker-compose.prod.yml"
            export NODE_ENV="production"
            export DEBUG="false"
            ;;
        *)
            export COMPOSE_FILE="docker-compose.yml"
            export NODE_ENV="development"
            export DEBUG="true"
            ;;
    esac

    log_info "Docker Compose files: $COMPOSE_FILE"
}

# Main function
main() {
    local ENVIRONMENT
    ENVIRONMENT=$(detect_environment "$1")

    log_info "Detected environment: $ENVIRONMENT"

    load_environment
    validate_environment
    setup_environment
    export_environment_info

    log_success "Environment setup complete for $ENVIRONMENT"
}

# Allow script to be sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed
    main "$@"
fi
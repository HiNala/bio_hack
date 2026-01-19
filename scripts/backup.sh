#!/bin/bash
# ScienceRAG Backup Script
# Creates backups of database and configuration

set -e

# Configuration
PROJECT_NAME="sciencerag"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${PROJECT_NAME}_backup_${TIMESTAMP}"

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

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

# Backup database
backup_database() {
    log_info "Backing up database..."

    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}_database.sql"

    # Use docker exec to run pg_dump
    docker compose exec -T postgres pg_dump \
        -U sciencerag \
        -d sciencerag \
        --no-password \
        --format=custom \
        --compress=9 \
        --file=/tmp/backup.dump

    # Copy backup from container
    docker compose cp postgres:/tmp/backup.dump "$BACKUP_FILE"

    # Clean up
    docker compose exec -T postgres rm -f /tmp/backup.dump

    # Verify backup
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_success "Database backup created: $BACKUP_FILE (${SIZE})"
    else
        log_error "Database backup failed"
        exit 1
    fi
}

# Backup configuration
backup_config() {
    log_info "Backing up configuration..."

    CONFIG_BACKUP_DIR="$BACKUP_DIR/${BACKUP_NAME}_config"

    mkdir -p "$CONFIG_BACKUP_DIR"

    # Backup environment files (excluding secrets)
    if [ -f ".env" ]; then
        cp .env "$CONFIG_BACKUP_DIR/.env.backup"
        log_info "Environment file backed up (secrets redacted)"
    fi

    # Backup docker-compose files
    cp docker-compose*.yml "$CONFIG_BACKUP_DIR/" 2>/dev/null || true

    # Backup configuration files
    cp -r docker/*.conf "$CONFIG_BACKUP_DIR/" 2>/dev/null || true
    cp docker/init-db.sql "$CONFIG_BACKUP_DIR/" 2>/dev/null || true

    log_success "Configuration backup created: $CONFIG_BACKUP_DIR"
}

# Backup uploads (if any)
backup_uploads() {
    log_info "Backing up uploads..."

    # Check if uploads volume exists
    if docker volume ls | grep -q "sciencerag.*uploads"; then
        UPLOAD_BACKUP_DIR="$BACKUP_DIR/${BACKUP_NAME}_uploads"
        mkdir -p "$UPLOAD_BACKUP_DIR"

        # This would require mounting the volume and copying files
        # For now, just note that uploads exist
        log_info "Uploads volume detected - manual backup may be required"
    else
        log_info "No uploads volume found"
    fi
}

# Create backup manifest
create_manifest() {
    MANIFEST_FILE="$BACKUP_DIR/${BACKUP_NAME}_manifest.txt"

    cat > "$MANIFEST_FILE" << EOF
ScienceRAG Backup Manifest
Created: $(date)
Backup ID: $BACKUP_NAME

Contents:
$(ls -la "$BACKUP_DIR" | grep "$BACKUP_NAME")

System Information:
- Hostname: $(hostname)
- User: $(whoami)
- Docker Version: $(docker --version)
- Docker Compose Version: $(docker compose version 2>/dev/null || docker-compose --version)

To restore:
1. Stop all services: docker compose down
2. Restore database: pg_restore -U sciencerag -d sciencerag < database_backup.sql
3. Restore configuration files
4. Start services: docker compose up -d
EOF

    log_success "Backup manifest created: $MANIFEST_FILE"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."

    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t | grep "${PROJECT_NAME}_backup_" | tail -n +11 | xargs -r rm -rf
    cd - > /dev/null

    log_success "Old backups cleaned up"
}

# Compress backup
compress_backup() {
    log_info "Compressing backup..."

    ARCHIVE_NAME="${BACKUP_NAME}.tar.gz"
    ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"

    # Create compressed archive
    tar -czf "$ARCHIVE_PATH" -C "$BACKUP_DIR" "$BACKUP_NAME"_*

    # Remove uncompressed files
    rm -rf "$BACKUP_DIR/${BACKUP_NAME}"_*

    SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
    log_success "Backup compressed: $ARCHIVE_PATH (${SIZE})"
}

# Main backup function
main() {
    log_info "Starting ScienceRAG backup..."

    create_backup_dir
    backup_database
    backup_config
    backup_uploads
    create_manifest

    if [ "${1:-compress}" = "compress" ]; then
        compress_backup
    fi

    cleanup_old_backups

    log_success "🎉 Backup completed successfully!"
    log_info ""
    log_info "Backup location: $BACKUP_DIR"
    log_info "Backup name: $BACKUP_NAME"

    # Show backup size
    if [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" ]; then
        SIZE=$(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
        log_info "Total backup size: $SIZE"
    fi
}

# Show usage
usage() {
    echo "ScienceRAG Backup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --no-compress    Don't compress the backup"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Create compressed backup"
    echo "  $0 --no-compress # Create uncompressed backup"
}

# Parse arguments
case "${1:-}" in
    "--help"|"-h")
        usage
        exit 0
        ;;
    "--no-compress")
        COMPRESS=false
        ;;
    *)
        COMPRESS=true
        ;;
esac

# Run main function
main ${COMPRESS:+compress}
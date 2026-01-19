# ScienceRAG Deployment & Maintenance Scripts

This directory contains scripts for deploying, monitoring, and maintaining the ScienceRAG application.

## 🚀 Deployment Scripts

### `deploy.sh`
Full deployment automation script for ScienceRAG.

**Usage:**
```bash
# Deploy to development
./deploy.sh development

# Deploy to production
./deploy.sh production

# Build images only
./deploy.sh development build

# Run migrations only
./deploy.sh development migrate

# Run health checks only
./deploy.sh development health
```

**Features:**
- Automated Docker image building
- Database migration execution
- Health check validation
- Environment-specific deployments
- Rollback capabilities

## 🔧 Maintenance Scripts

### `maintenance.sh`
Routine maintenance tasks for keeping ScienceRAG healthy.

**Usage:**
```bash
# Run all maintenance tasks
./maintenance.sh

# Clean up Docker resources only
./maintenance.sh docker

# Database maintenance
./maintenance.sh database

# Security audit
./maintenance.sh security
```

**Tasks:**
- Docker resource cleanup
- Log file rotation
- Database optimization
- Security audits
- Performance tuning

### `backup.sh`
Automated backup creation and management.

**Usage:**
```bash
# Create compressed backup
./backup.sh

# Create uncompressed backup
./backup.sh --no-compress
```

**Features:**
- Database backups using pg_dump
- Configuration file backups
- Automatic cleanup of old backups
- Backup verification

### `monitor.sh`
Real-time monitoring and health checking.

**Usage:**
```bash
# Run health checks once
./monitor.sh once

# Continuous monitoring
./monitor.sh continuous
```

**Monitors:**
- Docker service status
- API endpoint health
- Database connectivity
- System resource usage
- Docker container metrics
- Application logs

## ⚙️ Configuration

### Environment Variables

**For deployment:**
```bash
# Docker registry (optional)
DOCKER_REGISTRY=your-registry.com

# Database settings (for production)
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

**For monitoring:**
```bash
# Monitoring interval (seconds)
HEALTH_CHECK_INTERVAL=60

# Log file location
LOG_FILE=./logs/monitor_$(date +%Y%m%d).log
```

**For maintenance:**
```bash
# Force database reindexing (dangerous in production!)
FORCE_REINDEX=true
```

## 📋 Prerequisites

Before running these scripts, ensure you have:

1. **Docker & Docker Compose** installed
2. **Environment file** (`.env`) with required variables
3. **Proper permissions** to run Docker commands
4. **Network access** to required services

## 🔒 Security Notes

- Scripts include basic security checks
- Sensitive data is redacted in backups
- Database credentials should be in environment variables
- Regular security audits are recommended

## 📊 Logging

All scripts create detailed logs in the `./logs/` directory:

- `deploy_YYYYMMDD.log` - Deployment logs
- `monitor_YYYYMMDD.log` - Monitoring logs
- `maintenance_YYYYMMDD.log` - Maintenance logs

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Make scripts executable (Linux/Mac)
   chmod +x scripts/*.sh
   ```

2. **Docker Not Found**
   - Ensure Docker Desktop is running
   - Check user permissions for Docker

3. **Database Connection Failed**
   - Verify PostgreSQL container is running
   - Check database credentials in `.env`

4. **Port Conflicts**
   - Ensure ports 3000, 8000, 5433, 6379 are available
   - Modify `docker-compose.yml` if needed

### Getting Help

For issues with these scripts:

1. Check the log files in `./logs/`
2. Run individual commands manually to debug
3. Verify Docker and environment setup
4. Check the main application logs: `docker compose logs`

## 🤝 Contributing

When adding new scripts:

1. Include comprehensive error handling
2. Add usage documentation
3. Follow the existing logging patterns
4. Test on both development and production environments
5. Update this README with new script information
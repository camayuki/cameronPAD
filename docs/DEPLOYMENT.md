# Production Deployment Guide

## 🎯 Overview

This guide covers deploying CameronPAD to production environments with proper security, performance, and monitoring configurations.

## 🏗️ Deployment Architecture

### Recommended Production Stack
- **Application**: FastAPI with Uvicorn/Gunicorn
- **Database**: PostgreSQL or SQLite for smaller deployments
- **Cache**: Redis for session storage and caching
- **Reverse Proxy**: Nginx for static files and SSL termination
- **Container**: Docker with Docker Compose
- **Monitoring**: Built-in health checks + external monitoring

### Infrastructure Options

#### Option 1: Single Server (Small Scale)
```
[Internet] → [Nginx] → [Docker Compose]
                     ├── CameronPAD App
                     ├── PostgreSQL
                     └── Redis
```

#### Option 2: Multi-Server (Large Scale)
```
[Internet] → [Load Balancer] → [App Servers]
                            ├── [Database Server]
                            ├── [Cache Server]
                            └── [File Storage]
```

## 🐳 Docker Production Setup

### Production Dockerfile
Create `docker/Dockerfile.prod`:
```dockerfile
FROM python:3.12-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements/production.txt .
RUN pip install --no-cache-dir --user -r production.txt

# Production image
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Copy Python packages from builder
COPY --from=builder /home/app/.local /home/app/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Switch to app user
USER app

# Add user packages to PATH
ENV PATH=/home/app/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Command
CMD ["gunicorn", "app_new.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Production Docker Compose
Create `docker-compose.prod.yaml`:
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile.prod
    container_name: cameronpad_app
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://cameronpad:${DB_PASSWORD}@db:5432/cameronpad
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - FINNHUB_TOKEN=${FINNHUB_TOKEN}
      - ALPHA_VANTAGE_KEY=${ALPHA_VANTAGE_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - db
      - redis
    networks:
      - cameronpad_network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.cameronpad.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.cameronpad.tls=true"
      - "traefik.http.routers.cameronpad.tls.certresolver=letsencrypt"

  db:
    image: postgres:15-alpine
    container_name: cameronpad_db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=cameronpad
      - POSTGRES_USER=cameronpad
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - cameronpad_network
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c pg_stat_statements.track=all
      -c max_connections=200

  redis:
    image: redis:7-alpine
    container_name: cameronpad_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - cameronpad_network

  nginx:
    image: nginx:alpine
    container_name: cameronpad_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/var/www/static:ro
      - ./data/uploads:/var/www/uploads:ro
    depends_on:
      - app
    networks:
      - cameronpad_network

  # Optional: Reverse proxy with automatic SSL
  traefik:
    image: traefik:v2.10
    container_name: cameronpad_traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik:/etc/traefik
      - ./ssl:/ssl
    networks:
      - cameronpad_network
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.letsencrypt.acme.tlschallenge=true
      - --certificatesresolvers.letsencrypt.acme.email=your-email@domain.com
      - --certificatesresolvers.letsencrypt.acme.storage=/ssl/acme.json

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  cameronpad_network:
    driver: bridge
```

## 🔧 Nginx Configuration

Create `nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream cameronpad_app {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";

    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

        # Security
        client_max_body_size 10M;
        
        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /uploads/ {
            alias /var/www/uploads/;
            expires 1d;
            add_header Cache-Control "public";
        }

        # API rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://cameronpad_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login rate limiting
        location /api/v1/auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://cameronpad_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Application
        location / {
            proxy_pass http://cameronpad_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check endpoint (no rate limiting)
        location /health {
            proxy_pass http://cameronpad_app;
            access_log off;
        }
    }
}
```

## 🔐 Security Configuration

### Environment Variables
Create `.env.prod`:
```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-this
DEBUG=false

# Database
DATABASE_URL=postgresql://cameronpad:your-db-password@db:5432/cameronpad
DB_PASSWORD=your-db-password

# Cache
REDIS_URL=redis://:your-redis-password@redis:6379
REDIS_PASSWORD=your-redis-password

# External APIs
FINNHUB_TOKEN=your-finnhub-token
ALPHA_VANTAGE_KEY=your-alpha-vantage-key

# Notifications (optional)
DISCORD_WEBHOOK_URL=your-discord-webhook
TELEGRAM_BOT_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/cameronpad.log

# Upload limits
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=/app/data/uploads
```

### SSL Certificate Setup

#### Option 1: Let's Encrypt (Automated)
```bash
# Using Traefik (automatic)
# Configuration included in docker-compose.prod.yaml

# Using Certbot (manual)
certbot --nginx -d your-domain.com
```

#### Option 2: Custom Certificates
```bash
# Generate self-signed for testing
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem
```

## 🚀 Deployment Process

### Initial Deployment
```bash
# 1. Clone repository
git clone https://github.com/your-repo/cameronpad.git
cd cameronpad

# 2. Configure environment
cp .env.example .env.prod
# Edit .env.prod with your values

# 3. Create required directories
mkdir -p {data,logs,backups,ssl}
chmod 755 data logs
chmod 700 ssl

# 4. Build and start services
docker-compose -f docker-compose.prod.yaml up -d

# 5. Initialize database
docker-compose -f docker-compose.prod.yaml exec app \
    python -c "from app_new.core.database import initialize_database; initialize_database()"

# 6. Create admin user
docker-compose -f docker-compose.prod.yaml exec app \
    python scripts/create_admin.py

# 7. Verify deployment
curl https://your-domain.com/health
```

### Update Deployment
```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild and restart
docker-compose -f docker-compose.prod.yaml build app
docker-compose -f docker-compose.prod.yaml up -d app

# 3. Run migrations if needed
docker-compose -f docker-compose.prod.yaml exec app \
    python scripts/migrate.py

# 4. Verify update
curl https://your-domain.com/health
```

### Rollback Deployment
```bash
# 1. Revert to previous version
git checkout previous-stable-tag

# 2. Rebuild and restart
docker-compose -f docker-compose.prod.yaml build app
docker-compose -f docker-compose.prod.yaml up -d app
```

## 📊 Monitoring & Observability

### Health Checks
```bash
# Application health
curl https://your-domain.com/health

# System status
curl https://your-domain.com/api/v1/admin/system/status

# Plugin health
curl https://your-domain.com/api/v1/admin/plugins
```

### Log Management
```bash
# View application logs
docker-compose -f docker-compose.prod.yaml logs -f app

# View specific plugin logs
docker-compose -f docker-compose.prod.yaml logs -f app | grep "stocks"

# Rotate logs
docker-compose -f docker-compose.prod.yaml exec app \
    logrotate /etc/logrotate.conf
```

### Performance Monitoring
```bash
# Database performance
docker-compose -f docker-compose.prod.yaml exec db \
    psql -U cameronpad -d cameronpad -c "SELECT * FROM pg_stat_activity;"

# Redis performance
docker-compose -f docker-compose.prod.yaml exec redis \
    redis-cli info stats

# Application metrics
curl https://your-domain.com/api/v1/admin/system/metrics
```

### External Monitoring
```yaml
# docker-compose.monitoring.yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - cameronpad_network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - cameronpad_network

volumes:
  grafana_data:

networks:
  cameronpad_network:
    external: true
```

## 💾 Backup & Recovery

### Database Backup
Create `scripts/backup.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cameronpad_backup_${DATE}.sql"

# Create backup
docker-compose -f docker-compose.prod.yaml exec -T db \
    pg_dump -U cameronpad cameronpad > "${BACKUP_DIR}/${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Remove old backups (keep 30 days)
find ${BACKUP_DIR} -name "cameronpad_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Application Data Backup
```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup application data
tar -czf "${BACKUP_DIR}/app_data_${DATE}.tar.gz" \
    data/ config/ logs/

# Backup uploads
tar -czf "${BACKUP_DIR}/uploads_${DATE}.tar.gz" \
    data/uploads/

echo "Data backup completed"
```

### Automated Backups
Add to crontab:
```bash
# Database backup daily at 2 AM
0 2 * * * /path/to/cameronpad/scripts/backup.sh

# Application data backup weekly
0 3 * * 0 /path/to/cameronpad/scripts/backup_data.sh
```

### Recovery Process
```bash
# 1. Stop application
docker-compose -f docker-compose.prod.yaml down

# 2. Restore database
gunzip -c cameronpad_backup_20231201_020000.sql.gz | \
    docker-compose -f docker-compose.prod.yaml exec -T db \
    psql -U cameronpad cameronpad

# 3. Restore application data
tar -xzf app_data_20231201_030000.tar.gz

# 4. Start application
docker-compose -f docker-compose.prod.yaml up -d

# 5. Verify recovery
curl https://your-domain.com/health
```

## 🔄 CI/CD Pipeline

### GitHub Actions
Create `.github/workflows/deploy.yaml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements/testing.txt
      
      - name: Run tests
        run: |
          pytest --cov=app_new
      
      - name: Security scan
        run: |
          bandit -r app_new/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to production
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/cameronpad
            git pull origin main
            docker-compose -f docker-compose.prod.yaml build app
            docker-compose -f docker-compose.prod.yaml up -d app
            
            # Health check
            sleep 30
            curl -f https://your-domain.com/health || exit 1
```

## 🔧 Performance Tuning

### Application Performance
```yaml
# config/environments/production.yaml
# Optimize for production

# Database connection pool
database:
  pool_size: 20
  max_overflow: 40
  pool_timeout: 30

# Cache configuration
cache:
  backend: redis
  default_ttl: 600
  max_keys: 10000

# Security settings
security:
  rate_limit_requests: 100
  rate_limit_period: 60
```

### Database Optimization
```sql
-- Enable query optimization
ANALYZE;

-- Create additional indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plugin_data_created_at 
    ON plugin_data(created_at);

-- Vacuum regularly
VACUUM ANALYZE;
```

### Redis Optimization
```bash
# redis.conf optimizations
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 🚨 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yaml logs app

# Common causes:
# - Missing environment variables
# - Database connection issues
# - Port conflicts
```

#### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.prod.yaml ps db

# Check database logs
docker-compose -f docker-compose.prod.yaml logs db

# Test connection
docker-compose -f docker-compose.prod.yaml exec app \
    python -c "from app_new.core.database import get_database_manager; print(get_database_manager().execute_query('SELECT 1'))"
```

#### Plugin Loading Issues
```bash
# Check plugin status
curl https://your-domain.com/api/v1/admin/plugins

# Reload specific plugin
curl -X POST https://your-domain.com/api/v1/admin/plugins/plugin_name/reload
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check slow queries
docker-compose -f docker-compose.prod.yaml exec db \
    psql -U cameronpad -d cameronpad -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## 📋 Maintenance Tasks

### Regular Maintenance
```bash
# Weekly maintenance script
#!/bin/bash

# Update system packages
apt update && apt upgrade -y

# Clean Docker resources
docker system prune -f

# Rotate logs
logrotate /etc/logrotate.conf

# Update SSL certificates
certbot renew

# Backup database
/path/to/backup.sh

# Check disk space
df -h
```

### Security Updates
```bash
# Update base images
docker-compose -f docker-compose.prod.yaml pull
docker-compose -f docker-compose.prod.yaml up -d

# Scan for vulnerabilities
docker scout cves cameronpad_app
```

This deployment guide provides a production-ready setup with security, performance, and monitoring best practices. Adjust configurations based on your specific requirements and infrastructure.
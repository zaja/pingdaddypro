# PingDaddyPro Development Setup

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/zaja/pingdaddypro)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-svejedobro%2Fpingdaddypro-blue?logo=docker)](https://hub.docker.com/r/svejedobro/pingdaddypro)
[![Version](https://img.shields.io/badge/Version-1.0.3-green)](https://github.com/zaja/pingdaddypro)

This document describes how to set up and run PingDaddyPro in development mode with PostgreSQL.

## Prerequisites

- Docker Desktop installed and running
- Git (optional, for version control)

## Quick Start

### Windows

1. **Start Development Environment:**
   ```cmd
   start-dev.bat
   ```
   Or using PowerShell:
   ```powershell
   .\dev.ps1 start
   ```

2. **Access Application:**
   - **Web Application:** http://localhost:5000
   - **Username:** `admin`
   - **Password:** `admin123`
   - **PostgreSQL:** localhost:5432
     - **Database:** `pingdaddypro`
     - **Username:** `pingdaddypro`
     - **Password:** `pingdaddypro`

> ⚠️ **Security Note:** Change the default password immediately after first login!

3. **View Logs:**
   ```cmd
   logs-dev.bat
   ```
   Or using PowerShell:
   ```powershell
   .\dev.ps1 logs
   ```

4. **Stop Development Environment:**
   ```cmd
   stop-dev.bat
   ```
   Or using PowerShell:
   ```powershell
   .\dev.ps1 stop
   ```

### Manual Docker Compose

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f pingdaddypro-dev

# Stop environment
docker-compose -f docker-compose.dev.yml down

# Reset database (removes all data)
docker-compose -f docker-compose.dev.yml down -v
```

## Development Features

- **Live Reload:** Code changes automatically restart the application
- **Debug Mode:** Flask debug mode enabled with detailed error messages
- **PostgreSQL Database:** Full PostgreSQL setup with persistent data
- **Development Logging:** Enhanced logging for debugging

## Database

### PostgreSQL Connection
- **Host:** localhost
- **Port:** 5432
- **Database:** `pingdaddypro`
- **Username:** `pingdaddypro`
- **Password:** `pingdaddypro`

### Accessing Database
```bash
# Connect to PostgreSQL
docker exec -it pingdaddypro-dev-postgres psql -U pingdaddypro -d pingdaddypro

# List tables
\dt

# View data
SELECT * FROM websites;
SELECT * FROM settings;
```


## Troubleshooting

### Container Issues
```bash
# Check container status
docker ps

# View all logs
docker-compose -f docker-compose.dev.yml logs

# Restart specific service
docker-compose -f docker-compose.dev.yml restart pingdaddypro-dev
```

### Database Issues
```bash
# Reset database completely
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

### Port Conflicts
If port 5000 or 5432 is already in use, modify the ports in `docker-compose.dev.yml`:

```yaml
services:
  pingdaddypro-dev:
    ports:
      - "5001:5000"  # Change to available port
  
  postgres:
    ports:
      - "5433:5432"  # Change to available port
```

## File Structure

```
pingdaddy/
├── docker-compose.dev.yml      # Development Docker Compose
├── Dockerfile.dev              # Development Dockerfile
├── start-dev.bat              # Windows start script
├── stop-dev.bat               # Windows stop script
├── logs-dev.bat               # Windows logs script
├── reset-dev-db.bat           # Windows database reset script
├── dev.ps1                    # PowerShell management script
└── .gitignore.dev             # Development gitignore
```

## Production Deployment

For production deployment, use the main `docker-compose.yml` file:

```bash
docker-compose up -d
```

This will start the application with PostgreSQL in production mode.

## 📚 Resources

- **GitHub Repository:** [https://github.com/zaja/pingdaddypro](https://github.com/zaja/pingdaddypro)
- **Docker Hub:** [https://hub.docker.com/r/svejedobro/pingdaddypro](https://hub.docker.com/r/svejedobro/pingdaddypro)
- **Issues:** [GitHub Issues](https://github.com/zaja/pingdaddypro/issues)
- **Discussions:** [GitHub Discussions](https://github.com/zaja/pingdaddypro/discussions)

## Contributing

1. Fork the repository on GitHub
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

For more information, see the main [README.md](README.md) file.





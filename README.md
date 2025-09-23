# Ping Daddy Pro - Professional Web Monitoring Application

![alt text](https://raw.githubusercontent.com/zaja/pingdaddypro/refs/heads/main/static/pingdaddylogo.png)

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/zaja/pingdaddypro)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-svejedobro%2Fpingdaddypro-blue?logo=docker)](https://hub.docker.com/r/svejedobro/pingdaddypro)
[![Version](https://img.shields.io/badge/Version-1.0.3-green)](https://github.com/zaja/pingdaddypro)

A comprehensive web monitoring application built with Flask and Docker, featuring real-time website monitoring, performance tracking, SSL certificate monitoring, and automated notifications with PostgreSQL database backend.

<!-- Trigger GitHub Actions -->

## 🚀 Features

- **Real-time Monitoring** - Monitor multiple websites simultaneously
- **WebSocket Integration** - Real-time frontend status updates using WebSocket instead of JavaScript refresh
- **Performance Tracking** - Track response times and performance metrics
- **SSL Certificate Monitoring** - Monitor SSL certificate expiration with configurable check frequency
- **SSL Check Frequency Setting** - User-configurable SSL certificate check interval in settings (optimized to avoid unnecessary frequent checks)
- **Automated Notifications** - Email and webhook notifications
- **Admin Authentication** - Secure admin login system
- **Dark/Light Theme** - Modern UI with theme support
- **Docker Support** - Easy deployment with Docker
- **PostgreSQL Database** - Scalable database backend

## 🚀 Quick Start

### Method 1: One-Line Install (Recommended)
```bash
# Download and run install script
curl -fsSL https://raw.githubusercontent.com/zaja/pingdaddypro/main/install.sh | bash
```

**Perfect for:** Most users, quick setup, automatic configuration

### Method 2: Docker Compose (Advanced)
```bash
# Clone repository and run with Docker Compose
git clone https://github.com/zaja/pingdaddypro.git
cd pingdaddypro
docker-compose up -d
```

**Perfect for:** Developers, custom configurations, source code access

## 🔄 Auto-Start After Reboot

**Yes! The application automatically starts after server restart.**

- **Docker Compose:** Uses `restart: unless-stopped` policy
- **Docker Run:** Use `--restart=unless-stopped` flag
- **Systemd:** Can be configured as system service

## 🔄 Updating the Application

**Both installation methods use the same Docker image, so updates are simple:**

### **Method 1: One-Line Install Update**
```bash
# Re-run the install script (it will update automatically)
curl -fsSL https://raw.githubusercontent.com/zaja/pingdaddypro/main/install.sh | bash
```

### **Method 2: Docker Compose Update**
```bash
# Navigate to your pingdaddypro directory
cd ~/pingdaddypro

# Update to latest version
docker-compose down
docker-compose pull
docker-compose up -d
```

**That's it!** Both methods will pull the latest `svejedobro/pingdaddypro:latest` image and restart the application.

**Important:** Updates preserve all your data (websites, webhooks, settings, history).

## 📊 Data Retention Policy

**Default retention periods:**
- **Monitoring History:** 30 days (detailed data)
- **SSL Certificates:** 1 year (certificate data)
- **Performance Metrics:** 1 year (aggregated data)

**Automatic cleanup:** Old data is automatically removed to maintain optimal performance.

**Custom retention:** Modify retention periods in the application settings.

**Storage impact:** See [Performance Guide](PERFORMANCE-GUIDE.md) for detailed storage requirements.

## 🌐 Access

- **Web Interface:** http://localhost:5000 or http://YOUR_IP:5000
- **Default Login:** admin / admin123
- **PostgreSQL:** localhost:5432 (user: pingdaddypro, password: pingdaddypro)

**Note:** Replace `YOUR_IP` with your server's IP address to access from other devices on the network.

## 🔧 Development Setup

For development with live reload and PostgreSQL:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Or use the convenience scripts:
# Windows: start-dev.bat
# PowerShell: .\dev.ps1 start
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup instructions.

## 🧹 Clean Installation

If you encounter issues with the installation, you can clean up Ping Daddy Pro Docker resources:

### Ping Daddy Pro Cleanup
```bash
# Stop PingDaddyPro containers (both installation methods)
docker stop pingdaddypro pingdaddypro-postgres pingdaddypro-nginx 2>/dev/null || true

# Remove PingDaddyPro containers
docker rm pingdaddypro pingdaddypro-postgres pingdaddypro-nginx 2>/dev/null || true

# Remove PingDaddyPro images
docker rmi svejedobro/pingdaddypro:latest 2>/dev/null || true

# Remove PingDaddyPro volumes
docker volume rm pingdaddypro_postgres_data 2>/dev/null || true

# Remove PingDaddyPro network
docker network rm pingdaddypro-network 2>/dev/null || true

# Remove local data directory
rm -rf ./pingdaddypro-data 2>/dev/null || true
rm -rf ./data 2>/dev/null || true

# Clean up Docker Compose (if used)
docker-compose down -v --remove-orphans 2>/dev/null || true
```

### Verify Cleanup
```bash
# Check if everything is removed
docker ps -a | grep pingdaddypro
docker images | grep pingdaddypro
docker volume ls | grep pingdaddypro
docker network ls | grep pingdaddypro

# Should return no results
```

After cleanup, you can start fresh with any installation method.

## 🔐 Default Access Credentials

### Web Application Access
- **URL:** http://localhost:5000 or http://YOUR_IP:5000
- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ **Security Note:** Change the default password immediately after first login!
> 
> **Network Access:** Use `YOUR_IP:5000` to access from other devices on the same network.

### PostgreSQL Database Access
- **Host:** localhost
- **Port:** 5432
- **Database:** `pingdaddypro`
- **Username:** `pingdaddypro`
- **Password:** `pingdaddypro`

## 🛡️ Security Features

**Authentication Security:**
- **Brute Force Protection:** Account locks after 4 failed login attempts
- **Lockout Duration:** 15 minutes automatic unlock
- **IP Tracking:** Monitors login attempts per IP address (10 attempts per IP in 15 minutes)
- **Password Hashing:** Uses bcrypt for secure password storage
- **IP Validation:** Validates IP addresses to prevent security issues
- **Security Logging:** Comprehensive logging of all login attempts

**Account Recovery:**
If your account gets locked due to failed attempts, you can unlock it via Docker:

```bash
# Method 1: Direct SQL command (Recommended)
docker exec -it pingdaddypro-postgres psql -U pingdaddypro -d pingdaddypro -c "UPDATE admin_users SET failed_attempts = 0, locked_until = NULL WHERE username = 'admin';"

# Method 2: Interactive PostgreSQL session
docker exec -it pingdaddypro-postgres psql -U pingdaddypro -d pingdaddypro

# Reset failed attempts and unlock account
UPDATE admin_users SET failed_attempts = 0, locked_until = NULL WHERE username = 'admin';

# Verify the unlock was successful
SELECT username, failed_attempts, locked_until FROM admin_users WHERE username = 'admin';

# Exit PostgreSQL
\q

# Restart application to clear any cached data
docker restart pingdaddypro
```

**Important:** After unlocking, restart the application container to ensure any cached lockout data is cleared.

**Note:** This is a simple authentication system suitable for internal use. For production environments, consider additional security measures like 2FA, stronger password policies, or integration with external authentication systems.

**Testing Brute Force Protection:**
The brute force protection can be tested by attempting multiple failed login attempts. The system will automatically lock the account after 4 failed attempts and unlock it after 15 minutes.

#### Connecting to PostgreSQL
```bash
# Using psql command line
psql -h localhost -p 5432 -U pingdaddypro -d pingdaddypro

# Using Docker exec
docker exec -it pingdaddypro-postgres psql -U pingdaddypro -d pingdaddypro
```

### Manual Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/pingdaddypro.git
cd pingdaddypro

# Install dependencies
pip install -r requirements.txt

# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://username:password@hostname:5432/database_name"

# Run application
python pingdaddypro.py
```

## 🔧 Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://pingdaddypro:pingdaddypro@localhost:5432/pingdaddypro` | PostgreSQL connection string |
| `FLASK_ENV` | `production` | Flask environment |
| `FLASK_DEBUG` | `false` | Enable debug mode |

### PostgreSQL Configuration
```bash
# Example DATABASE_URL for PostgreSQL
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
```

### Docker Volumes
| Volume | Description |
|--------|-------------|
| `/app/static` | Static files (logos, etc.) |

## 📊 Monitoring Features

- **Website Status** - Online/Offline detection
- **Performance Metrics** - Response time tracking
- **Content Monitoring** - Expected text verification
- **SSL Certificate** - Expiration monitoring
- **History Tracking** - Complete monitoring history
- **Export Data** - CSV export functionality

## 🔔 Notifications

### Email Notifications
- SMTP configuration
- Customizable email templates
- Event-specific notifications

### Webhook Notifications
- HTTP POST notifications
- HMAC signature verification
- Customizable payload format

## 🎨 UI Features

- **Responsive Design** - Works on all devices
- **Dark/Light Theme** - User preference
- **Real-time Updates** - Live monitoring status
- **Interactive Charts** - Performance visualization
- **Admin Panel** - Complete system management

## 🐳 Docker Images

- **Latest:** `ghcr.io/YOUR_USERNAME/pingdaddypro:latest`
- **Versioned:** `ghcr.io/YOUR_USERNAME/pingdaddypro:v1.0.0`
- **Multi-platform:** AMD64, ARM64

## 📚 Documentation

- [Docker Setup](DOCKER-DISTRIBUTION.md)
- [GHCR Setup](GHCR-Setup.md)
- [No Docker Compose](README-NoCompose.md)
- [Quick Start GHCR](QUICK-START-GHCR.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **GitHub Repository:** [https://github.com/zaja/pingdaddypro](https://github.com/zaja/pingdaddypro)
- **Docker Hub:** [https://hub.docker.com/r/svejedobro/pingdaddypro](https://hub.docker.com/r/svejedobro/pingdaddypro)
- **Issues:** [GitHub Issues](https://github.com/zaja/pingdaddypro/issues)
- **Discussions:** [GitHub Discussions](https://github.com/zaja/pingdaddypro/discussions)
- **Documentation:** [GitHub Wiki](https://github.com/zaja/pingdaddypro/wiki)

## 🚀 Automated Deployment

This repository includes GitHub Actions for automatic Docker Hub deployment:

- **Production Image:** `svejedobro/pingdaddypro:latest`
- **Development Image:** `svejedobro/pingdaddypro:dev`
- **Versioned Images:** `svejedobro/pingdaddypro:v1.0.0`

See [GITHUB-ACTIONS-SETUP.md](GITHUB-ACTIONS-SETUP.md) for detailed setup instructions.

## 📚 Documentation

- **[FAQ](FAQ.md)** - Frequently Asked Questions and detailed functionality guide
- **[Performance Guide](PERFORMANCE-GUIDE.md)** - Data generation patterns, PostgreSQL performance, and scaling recommendations
- **[GitHub Repository](https://github.com/zaja/pingdaddypro)** - Source code and development
- **[Docker Hub](https://hub.docker.com/r/svejedobro/pingdaddypro)** - Docker images

## 🙏 Acknowledgments

- Flask framework
- Bootstrap UI components
- Chart.js for visualizations
- Docker for containerization
- PostgreSQL for database

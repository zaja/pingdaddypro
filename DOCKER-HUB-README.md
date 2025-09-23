# Ping Daddy Pro - Professional Website Monitoring Tool

![alt text](https://raw.githubusercontent.com/zaja/pingdaddypro/refs/heads/main/static/pingdaddylogo.png)

A comprehensive Flask-based web application for monitoring website availability, SSL certificates, and performance metrics. Features real-time monitoring, webhook notifications, PostgreSQL database, and Docker containerization.

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

**Note:** Wait for PostgreSQL to fully start before running the application.

**To stop:**
```bash
docker stop pingdaddypro pingdaddypro-postgres pingdaddypro-nginx
docker rm pingdaddypro pingdaddypro-postgres pingdaddypro-nginx
```

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

## 🛡️ Security Features

**Authentication Security:**
- **Brute Force Protection:** Account locks after 4 failed login attempts
- **Lockout Duration:** 15 minutes automatic unlock
- **IP Tracking:** Monitors login attempts per IP address
- **Password Hashing:** Uses bcrypt for secure password storage

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

## ✨ Features

- **Real-time Website Monitoring** - Continuous uptime monitoring
- **SSL Certificate Tracking** - Expiration alerts and certificate details
- **Performance Metrics** - Response time tracking and analytics
- **Webhook Notifications** - Custom alerts via HTTP webhooks
- **PostgreSQL Database** - Reliable data storage
- **Modern Web Interface** - Bootstrap-based responsive UI
- **Docker Support** - Easy deployment and scaling

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Database:** PostgreSQL
- **Frontend:** Bootstrap, Chart.js
- **Containerization:** Docker
- **Monitoring:** Custom monitoring engine

## 📚 Documentation

- **[FAQ](FAQ.md)** - Frequently Asked Questions and detailed functionality guide
- **[Performance Guide](PERFORMANCE-GUIDE.md)** - Data generation patterns, PostgreSQL performance, and scaling recommendations
- **GitHub Repository:** https://github.com/zaja/pingdaddypro
- **Development Guide:** See DEVELOPMENT.md
- **Docker Compose:** Included for easy deployment

## 🔧 Configuration

The application uses environment variables for configuration:

```bash
DATABASE_URL=postgresql://pingdaddypro:pingdaddypro@db:5432/pingdaddypro
FLASK_ENV=production
```

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

## 📊 Monitoring

- **Uptime Monitoring** - Track website availability
- **SSL Certificate Monitoring** - Monitor certificate expiration
- **Performance Tracking** - Response time analytics
- **Custom Webhooks** - Integrate with your notification systems

## 🐳 Docker Tags

- `latest` - Production image
- `dev` - Development image with hot reload
- `v1.0.0` - Versioned releases

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues:** https://github.com/zaja/pingdaddypro/issues
- **Discussions:** https://github.com/zaja/pingdaddypro/discussions
- **Documentation:** https://github.com/zaja/pingdaddypro/wiki

---

**Version:** 1.0.3  
**Maintained by:** svejedobro  
**GitHub:** https://github.com/zaja/pingdaddypro

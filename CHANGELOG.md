# Changelog

All notable changes to PingDaddyPro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.3] - 2025-01-23

### Added
- **WebSocket Integration**: Real-time frontend status updates using WebSocket instead of JavaScript refresh
- **SSL Check Frequency Setting**: User-configurable SSL certificate check interval in settings
- **Performance Optimization**: Reduced unnecessary SSL checks to improve system performance

### Changed
- Frontend now uses WebSocket for real-time status updates
- SSL certificate monitoring frequency is now user-configurable
- Improved system performance by optimizing SSL check intervals

### Fixed
- Enhanced real-time monitoring capabilities
- Better resource utilization for SSL certificate checks

## [1.0.2] - 2025-01-23

### Fixed
- **CRITICAL**: Fixed admin user creation on fresh installations
- Added automatic database initialization on application startup
- Admin user (admin/admin123) is now created automatically when database is empty
- Improved brute force protection documentation

### Added
- GitHub Actions workflow for automatic releases
- Version management script (scripts/version.sh)
- Comprehensive security logging

### Changed
- Improved brute force protection documentation
- 
## [1.0.1] - 2025-01-23

### Fixed
- **CRITICAL**: Fixed brute force protection in Docker environment
- Fixed IP address detection behind reverse proxy (nginx)
- Fixed account lockout mechanism not working properly

### Added
- IP address validation to prevent security issues
- Enhanced security logging for all login attempts
- Cleanup function for old login attempts (30 days retention)
- API endpoint for resetting brute force lockout (`/api/reset-brute-force`)
- Comprehensive security documentation

### Security
- Account lockout after 4 failed attempts (15 minutes)
- IP lockout after 10 failed attempts from same IP (15 minutes)
- Automatic unlock after 15 minutes
- Manual unlock via database or API endpoint
- Proper IP address detection using X-Forwarded-For headers

## [1.0.0] - 2025-01-15

### Added
- Initial release of PingDaddyPro
- Real-time website monitoring
- SSL certificate monitoring
- Performance tracking
- Webhook notifications
- PostgreSQL database backend
- Docker containerization
- Admin authentication system
- Dark/Light theme support
- CSV export functionality
- Automated email notifications
- Performance charts and analytics

### Features
- Monitor multiple websites simultaneously
- Track response times and performance metrics
- Monitor SSL certificate expiration
- Send notifications via email and webhooks
- Responsive web interface
- Docker Compose deployment
- One-line installation script

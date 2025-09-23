# 📚 Ping Daddy Pro v1.0.3 - Frequently Asked Questions (FAQ)

## 🎯 Overview

This FAQ covers detailed functionality, configuration options, webhook management, backup/reset operations, data filtering, and performance monitoring in Ping Daddy Pro.

## 🔧 Configuration & Setup

### **Q: How does the authentication system work?**

**A:** Ping Daddy Pro uses a simple but secure authentication system:

**Login Process:**
1. **Default Credentials:** Username `admin`, Password `admin123`
2. **Password Security:** Passwords are hashed using bcrypt
3. **Session Management:** Login sessions are maintained using Flask sessions

**Security Features:**
- **Brute Force Protection:** Account locks after 4 failed login attempts
- **Lockout Duration:** 15 minutes automatic unlock
- **IP Tracking:** System monitors login attempts per IP address
- **Failed Attempt Logging:** All login attempts are logged for security monitoring

**Account Lockout Recovery:**
If your account gets locked due to failed attempts:

```bash
# Method 1: Wait 15 minutes (automatic unlock)
# The system will automatically unlock after 15 minutes

# Method 2: Manual unlock via Docker
docker exec -it pingdaddypro-postgres psql -U pingdaddypro -d pingdaddypro

# Reset failed attempts and unlock account
UPDATE admin_users SET failed_attempts = 0, locked_until = NULL WHERE username = 'admin';

# Exit PostgreSQL
\q
```

**Security Recommendations:**
- Change the default password immediately after first login
- Use strong passwords (minimum 8 characters, mixed case, numbers, symbols)
- Monitor login attempts regularly
- Consider additional security measures for production environments

### **Q: How do I add websites to monitor?**

**A:** Adding websites for monitoring:

1. **Access Websites:** Click "Websites" tab in the navigation
2. **Add Website:** Click "Add Website" button
3. **Configure Website:**
   - **Name:** Descriptive name for the website
   - **URL:** Full URL (including http:// or https://)
   - **Check Interval:** How often to check (1-300 seconds)
   - **Timeout:** Request timeout (1-30 seconds)
   - **Expected Text:** Optional text to search for on the page (separate from URL with |)
   - **SSL Monitoring:** Enable/disable SSL certificate monitoring
4. **Save Website:** Click "Save" to start monitoring

### **Q: How do I edit or delete websites?**

**A:** Managing existing websites:

1. **Access Websites:** Click "Websites" tab in the navigation
2. **Edit Website:** Click "Edit" button next to any website
3. **Modify Settings:** Update name, URL, interval, timeout, or expected text
4. **Save Changes:** Click "Save" to apply modifications
5. **Delete Website:** Click "Delete" button to remove website
6. **Confirm Deletion:** Confirm removal in the popup dialog

**Bulk Operations:**
- **Select Multiple:** Use checkboxes to select multiple websites
- **Bulk Edit:** Modify settings for multiple websites at once
- **Bulk Delete:** Remove multiple websites simultaneously

### **Q: How does the Expected Text feature work?**

**A:** Expected Text verification:

1. **Purpose:** Verify specific content is present on the webpage
2. **Configuration:** Enter text in the "Expected Text" field when adding/editing websites
3. **Format:** Separate Expected Text from URL using the pipe character (|)
4. **Behavior:** 
   - If text is found: Website marked as "up"
   - If text is not found: Website marked as "down"
5. **Use Cases:**
   - Verify login pages show "Welcome" message
   - Check for error messages like "Service Unavailable"
   - Confirm specific content is loading
   - Validate API responses contain expected data

**Format Examples:**
- **URL with Expected Text:** `https://example.com | Welcome`
- **URL only:** `https://example.com` (no expected text)
- **API with JSON:** `https://api.example.com/status | "status":"success"`
- **Login page:** `https://login.example.com | Dashboard`

**Examples:**
- **Login Page:** Expected text "Welcome" or "Dashboard"
- **Error Page:** Expected text "Service Available" (absence indicates error)
- **API Response:** Expected text "success" or specific JSON content
- **Status Page:** Expected text "All Systems Operational"

### **Q: How do I configure monitoring intervals?**

**A:** Monitoring intervals can be configured in the Settings page:

1. **Access Settings:** Click "Settings" tab in the top navigation
2. **Check Interval:** Set how often websites are checked (1-300 seconds)
3. **Timeout:** Set request timeout (1-30 seconds)
4. **Retry Count:** Number of retries before marking as down
5. **Save Settings:** Click "Save Settings" to apply changes

**Recommended intervals:**
- **Critical websites:** 30-60 seconds
- **Important websites:** 2-5 minutes
- **General monitoring:** 5-15 minutes

### **Q: How do I configure SSL certificate monitoring?**

**A:** SSL monitoring is enabled by default. To configure:

1. **Go to Settings:** Click "Settings" tab
2. **SSL Settings:** Enable/disable SSL certificate monitoring
3. **Warning Threshold:** Set days before expiry (default: 30 days)
4. **Critical Threshold:** Set critical warning days (default: 7 days)
5. **Save Settings:** Apply changes

**SSL monitoring checks:**
- Certificate validity
- Expiry dates
- Certificate chain
- SSL/TLS version

### **Q: How do I configure performance monitoring?**

**A:** Performance monitoring tracks response times and metrics:

1. **Settings Page:** Click "Settings" tab and enable performance monitoring
2. **Metrics Tracked:**
   - Response time (ms)
   - DNS lookup time
   - Connection time
   - First byte time
   - Total time
3. **Thresholds:** Set warning/critical response time limits
4. **Save Settings:** Apply configuration

## 🔗 Webhook Management

### **Q: How do I set up webhooks for notifications?**

**A:** Webhook setup for real-time notifications:

1. **Access Webhooks:** Click "Webhooks" in the navigation menu
2. **Add Webhook:** Click "Add Webhook" button
3. **Configure Webhook:**
   - **Name:** Descriptive name for the webhook
   - **URL:** Endpoint URL for notifications
   - **Events:** Select which events trigger the webhook
   - **Method:** HTTP method (POST, PUT, PATCH)
   - **Headers:** Custom headers (optional)
   - **Body Template:** Custom payload template (optional)
4. **Test Webhook:** Use "Test" button to verify configuration
5. **Save Webhook:** Click "Save" to activate

### **Q: What events can trigger webhooks?**

**A:** Available webhook events:

- **Website Down:** When a website goes offline
- **Website Up:** When a website comes back online
- **SSL Expiry Warning:** When SSL certificate expires soon
- **SSL Expiry Critical:** When SSL certificate expires very soon
- **Performance Alert:** When response time exceeds thresholds
- **Status Change:** Any status change (up/down)

### **Q: How do I customize webhook payloads?**

**A:** Custom payload templates:

1. **Body Template:** Use Jinja2 templating syntax
2. **Available Variables:**
   ```json
   {
     "event": "website_down",
     "website": {
       "id": 1,
       "name": "Example Site",
       "url": "https://example.com",
       "status": "down",
       "response_time": 5000,
       "last_check": "2024-01-15T10:30:00Z"
     },
     "timestamp": "2024-01-15T10:30:00Z"
   }
   ```
3. **Example Template:**
   ```json
   {
     "alert": "{{ event }}",
     "site": "{{ website.name }}",
     "url": "{{ website.url }}",
     "status": "{{ website.status }}",
     "time": "{{ timestamp }}"
   }
   ```

### **Q: How do I test webhook configurations?**

**A:** Testing webhooks:

1. **Test Button:** Click "Test" next to any webhook
2. **Manual Test:** Sends a test payload to verify configuration
3. **Check Logs:** View webhook delivery logs
4. **Troubleshooting:** Common issues and solutions

**Common webhook issues:**
- **404 Error:** Check URL endpoint
- **Authentication:** Verify API keys/headers
- **Timeout:** Check server response time
- **Format:** Verify payload structure

## 💾 Backup & Reset Operations

### **Q: How do I create a backup of my data?**

**A:** Creating backups:

1. **Access Backup:** Click "Backup" in the navigation menu
2. **Create Backup:** Click "Create Backup" button
3. **Backup Includes:**
   - Website configurations
   - Webhook settings
   - SSL certificates
   - Performance metrics
   - Monitoring history (optional)
4. **Download:** Backup file downloads automatically
5. **Storage:** Save backup file securely

**Backup file format:** JSON file with all configuration data

### **Q: How do I restore from a backup?**

**A:** Restoring from backup:

1. **Access Backup:** Click "Backup" in the navigation menu
2. **Upload Backup:** Click "Upload Backup" button
3. **Select File:** Choose your backup file
4. **Restore Options:**
   - **Full Restore:** All data and settings
   - **Settings Only:** Configuration without history
   - **Websites Only:** Website configurations only
5. **Confirm Restore:** Click "Restore" to proceed
6. **Verification:** Check restored data

**Important:** Restore will overwrite existing data!

### **Q: What does "Reset Everything" do?**

**A:** Complete system reset:

1. **Access Reset:** Click "Reset" in the navigation menu
2. **Reset Everything:** Click "Reset Everything" button
3. **Confirmation:** Type "RESET" to confirm
4. **Reset Process:**
   - Stops monitoring thread
   - Clears all website configurations
   - Removes all webhook settings
   - Deletes monitoring history
   - Resets SSL certificates
   - Clears performance metrics
   - Restarts monitoring thread

**Warning:** This action cannot be undone!

### **Q: How do I reset only specific data?**

**A:** Selective reset options:

1. **Reset Websites:** Clear only website configurations
2. **Reset Webhooks:** Clear only webhook settings
3. **Reset History:** Clear only monitoring history
4. **Reset SSL:** Clear only SSL certificate data
5. **Reset Performance:** Clear only performance metrics

**Selective reset:** Choose specific data types to reset

## 📊 Data Management & Filtering

### **Q: How do I filter monitoring history?**

**A:** History filtering options:

1. **Access History:** Click "History" in the navigation menu
2. **Filter Options:**
   - **Date Range:** Select start and end dates
   - **Website:** Filter by specific website
   - **Status:** Filter by status (up/down)
   - **Response Time:** Filter by response time range
   - **SSL Status:** Filter by SSL certificate status
3. **Apply Filters:** Click "Apply Filters" button
4. **Clear Filters:** Click "Clear Filters" to reset
5. **Export Filtered:** Export filtered data

### **Q: How do I export filtered data?**

**A:** Exporting filtered data:

1. **Apply Filters:** Set desired filters first
2. **Export Options:**
   - **CSV Format:** Comma-separated values
   - **JSON Format:** JavaScript Object Notation
   - **Excel Format:** Microsoft Excel compatible
3. **Export Button:** Click "Export" button
4. **Download:** File downloads automatically
5. **Data Included:**
   - Website information
   - Check timestamps
   - Status results
   - Response times
   - SSL information
   - Performance metrics

### **Q: How do I manage data retention?**

**A:** Data retention management:

1. **Settings Page:** Click "Settings" tab and access retention settings
2. **Retention Periods:**
   - **Monitoring History:** 30 days (default)
   - **SSL Certificates:** 1 year (default)
   - **Performance Metrics:** 1 year (default)
3. **Custom Retention:** Modify periods as needed
4. **Automatic Cleanup:** Old data removed automatically
5. **Manual Cleanup:** Force cleanup if needed

**Storage impact:** Longer retention = more storage usage

## ⚡ Performance Monitoring

### **Q: How do I access the Performance tab?**

**A:** Performance monitoring access:

1. **Navigation Menu:** Click "Performance" tab
2. **Performance Dashboard:** View real-time metrics
3. **Available Metrics:**
   - Response time trends
   - Uptime percentages
   - Error rates
   - SSL certificate status
   - Performance alerts
4. **Time Ranges:** Select different time periods
5. **Website Selection:** Filter by specific websites

### **Q: What performance metrics are tracked?**

**A:** Tracked performance metrics:

- **Response Time:** Total request time
- **DNS Lookup:** Domain name resolution time
- **Connection Time:** TCP connection establishment
- **First Byte Time:** Time to first response byte
- **SSL Handshake:** TLS/SSL negotiation time
- **Uptime Percentage:** Availability over time
- **Error Rate:** Failed request percentage

### **Q: How do I set performance alerts?**

**A:** Performance alert configuration:

1. **Settings Page:** Click "Settings" tab and access performance settings
2. **Alert Thresholds:**
   - **Warning Response Time:** Default 2 seconds
   - **Critical Response Time:** Default 5 seconds
   - **Uptime Threshold:** Default 99%
3. **Alert Methods:**
   - **Webhook Notifications:** Real-time alerts
   - **Email Notifications:** Email alerts (if configured)
   - **Dashboard Alerts:** Visual indicators
4. **Save Settings:** Apply alert configuration

### **Q: How do I interpret performance charts?**

**A:** Performance chart interpretation:

1. **Response Time Chart:**
   - **Green Line:** Average response time
   - **Red Dots:** Individual check results
   - **Yellow Line:** Warning threshold
   - **Red Line:** Critical threshold

2. **Uptime Chart:**
   - **Green Bars:** Uptime percentage
   - **Red Bars:** Downtime percentage
   - **Time Periods:** Hourly/daily/weekly views

3. **SSL Chart:**
   - **Green:** Valid certificates
   - **Yellow:** Expiring soon
   - **Red:** Expired certificates

## 🔄 Application Updates

### **Q: How do I update the application to the latest version?**

**A:** Updating Ping Daddy Pro is simple since both installation methods use the same Docker image:

#### **Method 1: One-Line Install Update**
```bash
# Re-run the install script (it will update automatically)
curl -fsSL https://raw.githubusercontent.com/zaja/pingdaddypro/main/install.sh | bash
```

#### **Method 2: Docker Compose Update**
```bash
# Navigate to your pingdaddypro directory
cd ~/pingdaddypro

# Update to latest version
docker-compose down
docker-compose pull
docker-compose up -d
```

**That's it!** Both methods will pull the latest `svejedobro/pingdaddypro:latest` image and restart the application.

### **Q: Will my data be preserved during updates?**

**A:** Yes! Updates preserve all your data:

- **Websites:** All configured websites remain
- **Webhooks:** All webhook configurations preserved
- **Settings:** All application settings maintained
- **History:** Monitoring history data preserved
- **SSL Certificates:** SSL certificate data maintained
- **Performance Metrics:** Performance data preserved

**Data is stored in PostgreSQL database container, which persists across updates.**

### **Q: How do I rollback to a previous version?**

**A:** Rolling back to previous version:

```bash
# List available image tags
docker images svejedobro/pingdaddypro

# Rollback to specific version
docker-compose down
docker-compose up -d --image svejedobro/pingdaddypro:v1.0.0

# Or with docker run
docker stop pingdaddypro
docker rm pingdaddypro
docker run -d --name pingdaddypro \
  --network pingdaddypro-network \
  -e DATABASE_URL=postgresql://pingdaddypro:pingdaddypro@pingdaddypro-postgres:5432/pingdaddypro \
  -p 5000:5000 \
  --restart=unless-stopped \
  svejedobro/pingdaddypro:v1.0.0
```

### **Q: How do I check if an update is available?**

**A:** Checking for updates:

```bash
# Check current version
docker exec pingdaddypro python -c "
import requests
response = requests.get('http://localhost:5000/api/version')
print('Current version:', response.json()['version'])
"

# Check latest version on Docker Hub
docker pull svejedobro/pingdaddypro:latest
docker images svejedobro/pingdaddypro

# Compare versions
docker inspect svejedobro/pingdaddypro:latest | grep -i created
```

### **Q: What should I do before updating?**

**A:** Pre-update checklist:

1. **Backup Data (Optional):**
   ```bash
# Create backup
docker exec pingdaddypro python -c "
import json
import psycopg2
conn = psycopg2.connect('postgresql://pingdaddypro:pingdaddypro@pingdaddypro-postgres:5432/pingdaddypro')
cursor = conn.cursor()
# Export data logic here
print('Backup completed')
"
   ```

2. **Check Current Status:**
   ```bash
   # Verify application is running
   docker-compose ps
   
# Check logs for errors
docker-compose logs pingdaddypro | tail -20
   ```

3. **Note Current Configuration:**
   - Website configurations
   - Webhook settings
   - Custom settings

### **Q: What should I do after updating?**

**A:** Post-update verification:

1. **Verify Application Started:**
   ```bash
   # Check container status
   docker-compose ps
   
# Check logs
docker-compose logs pingdaddypro | tail -20
   ```

2. **Test Application:**
   - Access web interface
   - Check website monitoring
   - Test webhook functionality
   - Verify settings

3. **Check Data Integrity:**
   ```bash
# Verify database connection
docker-compose logs pingdaddypro | grep -i "database\|error\|success"
   ```

### **Q: How often should I update?**

**A:** Update recommendations:

- **Security Updates:** Update immediately when available
- **Feature Updates:** Update when new features are needed
- **Bug Fixes:** Update when experiencing issues
- **Regular Updates:** Monthly or quarterly updates recommended

**Check for updates regularly:**
```bash
# Check for updates weekly
docker pull svejedobro/pingdaddypro:latest
docker images svejedobro/pingdaddypro
```

### **Q: I get "Can't find a suitable configuration file" error when updating?**

**A:** This error means you're not in the correct directory for Method 2:

#### **Solution 1: Navigate to correct directory**
```bash
# Find your pingdaddypro directory
find ~ -name "pingdaddypro" -type d 2>/dev/null

# Navigate to that directory
cd ~/pingdaddypro

# Run update
docker-compose down
docker-compose pull
docker-compose up -d
```

#### **Solution 2: Use Method 1 instead**
```bash
# If you can't find the directory, use the install script
curl -fsSL https://raw.githubusercontent.com/zaja/pingdaddypro/main/install.sh | bash
```

#### **Solution 3: Clone fresh**
```bash
# Clone repository fresh
git clone https://github.com/zaja/pingdaddypro.git
cd pingdaddypro
docker-compose up -d
```

## 🔍 Troubleshooting

### **Q: Why is my website showing as down when it's actually up?**

**A:** Common causes and solutions:

1. **Check Interval:** Website might be slow to respond
2. **Timeout Settings:** Increase timeout if needed
3. **Network Issues:** Check your server's internet connection
4. **DNS Problems:** Verify DNS resolution
5. **SSL Issues:** Check SSL certificate validity
6. **Firewall:** Ensure ports are open

**Debugging steps:**
- Check monitoring logs
- Test website manually
- Verify network connectivity
- Review timeout settings

### **Q: Why are webhooks not working?**

**A:** Webhook troubleshooting:

1. **Check URL:** Verify endpoint URL is correct
2. **Test Connection:** Use "Test" button
3. **Check Logs:** View webhook delivery logs
4. **Verify Headers:** Check authentication headers
5. **Check Payload:** Verify payload format
6. **Network Issues:** Ensure endpoint is accessible

**Common solutions:**
- Update webhook URL
- Check authentication
- Verify payload format
- Test endpoint manually

### **Q: How do I check application logs?**

**A:** Viewing application logs:

1. **Docker Logs:** `docker logs pingdaddypro`
2. **Database Logs:** `docker logs pingdaddypro-postgres`
3. **Application Logs:** Check web interface logs
4. **Error Logs:** Look for error messages
5. **Debug Mode:** Enable debug logging if needed

**Log locations:**
- Application: Docker container logs
- Database: PostgreSQL logs
- Web server: Nginx logs (if used)

### **Q: How do I restart the application?**

**A:** Restarting the application:

1. **Docker Compose:** `docker-compose restart`
2. **Docker Run:** `docker restart pingdaddypro`
3. **Full Restart:** `docker-compose down && docker-compose up -d`
4. **Database Restart:** `docker restart pingdaddypro-postgres`
5. **Verify Status:** Check container status

**Restart reasons:**
- Configuration changes
- Performance issues
- Memory problems
- Update installation

## 📈 Advanced Features

### **Q: How do I set up multiple monitoring intervals per website?**

**A:** Advanced monitoring configuration:

1. **Individual Settings:** Each website can have custom intervals
2. **Priority Levels:** Set different intervals for different priorities
3. **Time-based Monitoring:** Different intervals for different times
4. **Conditional Monitoring:** Monitor based on conditions
5. **Group Monitoring:** Monitor groups of websites together

### **Q: How do I configure custom SSL validation?**

**A:** Custom SSL validation:

1. **Settings Page:** Click "Settings" tab and access SSL configuration
2. **Custom Validation:** Enable custom validation rules
3. **Validation Rules:**
   - Certificate chain validation
   - Custom CA validation
   - Certificate pinning
   - Custom expiry rules
4. **Save Configuration:** Apply custom rules

### **Q: How do I set up monitoring groups?**

**A:** Website grouping:

1. **Create Groups:** Define monitoring groups
2. **Group Settings:** Configure group-specific settings
3. **Group Alerts:** Set group-level alerts
4. **Group Reports:** Generate group reports
5. **Group Management:** Manage group memberships

## 🚀 Best Practices

### **Q: What are the recommended monitoring practices?**

**A:** Best practices:

1. **Start Small:** Begin with few websites
2. **Gradual Scaling:** Add websites gradually
3. **Monitor Performance:** Watch system performance
4. **Regular Backups:** Create regular backups
5. **Test Webhooks:** Verify webhook functionality
6. **Review Logs:** Check logs regularly
7. **Update Regularly:** Keep application updated

### **Q: How do I optimize performance for large deployments?**

**A:** Performance optimization:

1. **Resource Allocation:** Allocate sufficient resources
2. **Database Optimization:** Optimize PostgreSQL settings
3. **Monitoring Intervals:** Use appropriate intervals
4. **Data Retention:** Set appropriate retention periods
5. **Load Balancing:** Use load balancing for high traffic
6. **Caching:** Implement caching strategies
7. **Monitoring:** Monitor system performance

### **Q: How do I ensure high availability?**

**A:** High availability setup:

1. **Multiple Instances:** Run multiple application instances
2. **Load Balancer:** Use load balancer for distribution
3. **Database Clustering:** Set up database clustering
4. **Backup Strategy:** Implement backup strategy
5. **Monitoring:** Monitor all components
6. **Failover:** Set up automatic failover
7. **Testing:** Regular failover testing

## 📞 Support & Resources

### **Q: Where can I get help?**

**A:** Support resources:

1. **GitHub Issues:** Report bugs and request features
2. **Documentation:** Read comprehensive documentation
3. **Performance Guide:** Check performance recommendations
4. **Community:** Join user community discussions
5. **Professional Support:** Contact for enterprise support

### **Q: How do I contribute to the project?**

**A:** Contributing to Ping Daddy Pro:

1. **Fork Repository:** Fork the GitHub repository
2. **Create Branch:** Create feature branch
3. **Make Changes:** Implement your changes
4. **Test Changes:** Test your modifications
5. **Submit PR:** Submit pull request
6. **Code Review:** Participate in code review
7. **Documentation:** Update documentation if needed

---

**💡 Tip:** This FAQ is regularly updated. Check back for new questions and answers.

**🔧 Support:** For additional help, check the GitHub repository issues or create a new issue.

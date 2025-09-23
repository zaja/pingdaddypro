from flask import Flask, render_template, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit
import threading
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from datetime import datetime, timedelta, timezone
import ssl
from urllib.parse import urlparse
import dns.resolver
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import socket
import traceback
import io
import base64
import hmac

# Application version
APP_VERSION = "1.0.3"
BUILD_DATE = "2025-01-24"
GIT_COMMIT = "ece612a"  # This can be updated during deployment
import hashlib
from io import BytesIO
import matplotlib
import pytz
from pytz import timezone as pytz_timezone
import tzlocal  # Za automatsko prepoznavanje lokalne vremenske zone
import bcrypt
import secrets
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dateutil import parser as dateutil_parser
matplotlib.use('Agg')  # Use non-GUI backend

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://pingdaddypro:pingdaddypro@localhost:5432/pingdaddypro')

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        return psycopg2.connect(DATABASE_URL, connection_factory=psycopg2.extras.RealDictConnection)
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e

def get_db_cursor():
    """Get PostgreSQL database cursor"""
    conn = get_db_connection()
    return conn.cursor(), conn

def get_client_ip():
    """Get the real client IP address, handling reverse proxy setups"""
    # Check for X-Forwarded-For header first (for reverse proxy setups)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one (original client)
        ip_address = forwarded_for.split(',')[0].strip()
        if ip_address and is_valid_ip(ip_address):
            return ip_address
    
    # Check for X-Real-IP header (alternative header used by some proxies)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip and is_valid_ip(real_ip.strip()):
        return real_ip.strip()
    
    # Fallback to request.remote_addr
    return request.remote_addr

def is_valid_ip(ip_address):
    """Validate if the given string is a valid IP address"""
    import socket
    try:
        # Try to parse as IPv4 or IPv6
        socket.inet_aton(ip_address)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip_address)
            return True
        except socket.error:
            return False
def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def is_account_locked(username, ip_address):
    """Check if account is locked due to brute force attempts"""
    try:
        # Validate IP address
        if not is_valid_ip(ip_address):
            print(f"WARNING: Invalid IP address detected: {ip_address}")
            ip_address = "invalid_ip"  # Use fallback for invalid IPs
        
        print(f"DEBUG LOCK CHECK: Checking lock for username={username}, ip={ip_address}")
        cursor, conn = get_db_cursor()
        
        # Check user lockout
        cursor.execute('SELECT failed_attempts, locked_until FROM admin_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        print(f"DEBUG LOCK CHECK: User data: {user}")
        
        if user and user['locked_until']:
            # Check if lockout has expired (15 minutes)
            if datetime.now() < user['locked_until']:
                print(f"DEBUG LOCK CHECK: Account locked until {user['locked_until']}")
                conn.close()
                return True
            else:
                # Lockout expired, reset it
                print(f"DEBUG LOCK CHECK: Lockout expired, resetting")
                cursor.execute('UPDATE admin_users SET failed_attempts = 0, locked_until = NULL WHERE username = %s', (username,))
                conn.commit()
        
        # Check IP-based lockout (last 15 minutes)
        fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
        cursor.execute('''SELECT COUNT(*) FROM login_attempts 
                         WHERE ip_address = %s AND attempt_time > %s AND success = FALSE''', 
                      (ip_address, fifteen_minutes_ago))
        ip_attempts = cursor.fetchone()['count']
        
        print(f"DEBUG LOCK CHECK: IP attempts in last 15 min: {ip_attempts}")
        
        conn.close()
        
        # Lock IP if more than 10 failed attempts in 15 minutes
        ip_locked = ip_attempts >= 10
        print(f"DEBUG LOCK CHECK: IP locked: {ip_locked}")
        return ip_locked
        
    except Exception as e:
        print(f"ERROR in is_account_locked: {str(e)}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        # In case of error, assume account is locked for security
        print(f"SECURITY: Assuming account is locked due to database error")
        return True

def record_login_attempt(username, ip_address, success):
    """Record a login attempt"""
    try:
        # Validate IP address
        if not is_valid_ip(ip_address):
            print(f"WARNING: Invalid IP address detected: {ip_address}")
            ip_address = "invalid_ip"  # Use fallback for invalid IPs
        
        cursor, conn = get_db_cursor()
        cursor.execute('''INSERT INTO login_attempts (ip_address, username, success) 
                         VALUES (%s, %s, %s)''', (ip_address, username, success))
        conn.commit()
        conn.close()
        
        # Log security event
        status = "SUCCESS" if success else "FAILED"
        print(f"SECURITY LOG: Login attempt - IP: {ip_address}, Username: {username}, Status: {status}")
        
    except Exception as e:
        print(f"ERROR recording login attempt: {str(e)}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        # Continue execution even if logging fails

def handle_failed_login(username, ip_address):
    """Handle failed login attempt and implement lockout"""
    try:
        print(f"DEBUG FAILED LOGIN: Handling failed login for {username} from {ip_address}")
        cursor, conn = get_db_cursor()
        
        # Increment failed attempts
        cursor.execute('''UPDATE admin_users SET failed_attempts = failed_attempts + 1 
                         WHERE username = %s''', (username,))
        
        # Check if we need to lock the account (4 failed attempts)
        cursor.execute('SELECT failed_attempts FROM admin_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        print(f"DEBUG FAILED LOGIN: Current failed attempts: {user['failed_attempts'] if user else 'No user found'}")
        
        if user and user['failed_attempts'] >= 4:
            # Lock account for 15 minutes
            lockout_until = datetime.now() + timedelta(minutes=15)
            cursor.execute('''UPDATE admin_users SET locked_until = %s 
                             WHERE username = %s''', (lockout_until, username))
            print(f"DEBUG FAILED LOGIN: Account {username} locked until {lockout_until}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"ERROR handling failed login: {str(e)}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        # Continue execution even if lockout fails

def reset_failed_attempts(username):
    """Reset failed attempts after successful login"""
    try:
        cursor, conn = get_db_cursor()
        cursor.execute('''UPDATE admin_users SET failed_attempts = 0, locked_until = NULL 
                         WHERE username = %s''', (username,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error resetting failed attempts: {str(e)}")

def login_user(username, password, ip_address):
    """Authenticate user and return success status"""
    try:
        # Check if account is locked
        if is_account_locked(username, ip_address):
            return False
        
        cursor, conn = get_db_cursor()
        cursor.execute('SELECT id, username, password_hash FROM admin_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user['password_hash']):
            # Successful login - reset failed attempts and update last login
            reset_failed_attempts(username)
            cursor, conn = get_db_cursor()
            cursor.execute('UPDATE admin_users SET last_login = %s WHERE id = %s', 
                         (datetime.now(), user['id']))
            conn.commit()
            conn.close()
            record_login_attempt(username, ip_address, True)
            return True
        else:
            # Failed login - record attempt and handle lockout
            record_login_attempt(username, ip_address, False)
            handle_failed_login(username, ip_address)
        return False
    except Exception as e:
        print(f"Login error: {str(e)}")
        record_login_attempt(username, ip_address, False)
        return False

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def init_db():
    try:
        cursor, conn = get_db_cursor()
        
        # PostgreSQL table creation
        cursor.execute('''CREATE TABLE IF NOT EXISTS websites
                         (id SERIAL PRIMARY KEY, url TEXT, expected_text TEXT)''')
        
        # Add ssl_check_interval column if it doesn't exist (migration)
        print("DEBUG: Starting SSL check interval migration...")
        try:
            # First check if settings table exists
            cursor.execute('''SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'settings'
            )''')
            result = cursor.fetchone()
            print(f"DEBUG: result from EXISTS query: {result}")
            table_exists = result['exists'] if result else False
            print(f"DEBUG: settings table exists: {table_exists}")
            
            if table_exists:
                # Check if column already exists
                cursor.execute('''SELECT column_name FROM information_schema.columns 
                                 WHERE table_name='settings' AND column_name='ssl_check_interval' ''')
                column_exists = cursor.fetchone() is not None
                print(f"DEBUG: ssl_check_interval column exists: {column_exists}")
                
                if not column_exists:
                    print("DEBUG: Adding ssl_check_interval column...")
                    cursor.execute('ALTER TABLE settings ADD COLUMN ssl_check_interval INTEGER DEFAULT 3600')
                    conn.commit()
                    print("Added ssl_check_interval column to settings table")
                else:
                    print("ssl_check_interval column already exists")
            else:
                print("Settings table doesn't exist yet, will be created with ssl_check_interval column")
        except Exception as e:
            print(f"Error checking/adding ssl_check_interval column: {e}")
            import traceback
            traceback.print_exc()
            # Don't rollback here, just continue
            pass
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                         (id SERIAL PRIMARY KEY, check_interval INTEGER, timeout INTEGER, 
                     expected_status INTEGER, performance_threshold INTEGER, consecutive_checks INTEGER,
                     smtp_server TEXT, smtp_port INTEGER, smtp_security TEXT,
                     smtp_user TEXT, smtp_pass TEXT, recipient_email TEXT,
                     from_name TEXT, subject_prefix TEXT, notification_method TEXT,
                     timezone TEXT, time_format TEXT, theme TEXT, email_events TEXT,
                     ssl_check_interval INTEGER DEFAULT 3600)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS webhooks
                         (id SERIAL PRIMARY KEY, name TEXT, url TEXT, secret TEXT,
                         events TEXT, active BOOLEAN DEFAULT TRUE)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS history
                         (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                         website TEXT, status TEXT, response_time INTEGER, details TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS performance_data
                         (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                         website TEXT, status TEXT, response_time INTEGER, details TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS ssl_certificates
                         (id SERIAL PRIMARY KEY, website TEXT, valid_from TIMESTAMP, 
                         valid_to TIMESTAMP, issuer TEXT, last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_users
                         (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, 
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP,
                         failed_attempts INTEGER DEFAULT 0, locked_until TIMESTAMP NULL)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS login_attempts
                         (id SERIAL PRIMARY KEY, ip_address TEXT, username TEXT, 
                         attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, success BOOLEAN)''')
        
        # Database migration - add missing columns if they don't exist
        try:
            # Check if failed_attempts column exists in admin_users
            cursor.execute('''SELECT column_name FROM information_schema.columns 
                             WHERE table_name='admin_users' AND column_name='failed_attempts' ''')
            if not cursor.fetchone():
                print("Adding failed_attempts column to admin_users table...")
                cursor.execute('ALTER TABLE admin_users ADD COLUMN failed_attempts INTEGER DEFAULT 0')
            
            # Check if locked_until column exists in admin_users
            cursor.execute('''SELECT column_name FROM information_schema.columns 
                             WHERE table_name='admin_users' AND column_name='locked_until' ''')
            if not cursor.fetchone():
                print("Adding locked_until column to admin_users table...")
                cursor.execute('ALTER TABLE admin_users ADD COLUMN locked_until TIMESTAMP NULL')
            
            print("Database migration completed successfully")
            
        except Exception as e:
            print(f"Database migration error: {str(e)}")
            # Continue execution even if migration fails
        
        # Create default admin user if none exists
        cursor.execute('SELECT COUNT(*) FROM admin_users')
        count_result = cursor.fetchone()
        user_count = count_result['count']
        if user_count == 0:
            default_password = 'admin123'
            password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''INSERT INTO admin_users (username, password_hash) 
                             VALUES (%s, %s)''', ('admin', password_hash))
            print("Created default admin user: admin / admin123")
        
        # Create default settings if none exist
        cursor.execute('SELECT COUNT(*) FROM settings')
        count_result = cursor.fetchone()
        settings_count = count_result['count']
        if settings_count == 0:
            try:
                local_tz = tzlocal.get_localzone().zone
            except:
                local_tz = 'UTC'
                
            cursor.execute('''INSERT INTO settings 
                         (check_interval, timeout, expected_status, performance_threshold, consecutive_checks,
                         smtp_server, smtp_port, smtp_security, smtp_user, smtp_pass, recipient_email,
                         from_name, subject_prefix, notification_method, timezone, time_format, theme, email_events, ssl_check_interval)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                             (60, 5, 200, 1000, 2, '', 587, 'TLS', '', '', '', '', 'PingDaddyPro:', 'both', 
                              local_tz, '%Y-%m-%d %H:%M:%S', 'light', '["Back Online", "Offline", "Content Error", "Performance", "SSL Expiration"]', 3600))
            print("Created default settings")
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        traceback.print_exc()

class WebsiteMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.websites = []
        self.website_expected_texts = {}
        self.website_status = {}
        self.last_check_times = {}
        self.response_times = {}
        self.performance_data = {}
        self.ssl_last_check_times = {}  # Track last SSL check time for each website
        self.webhooks = []
        self.monitor_thread = None
        self.notification_method = 'both'
        self.user_timezone = 'UTC'
        self.time_format = '%Y-%m-%d %H:%M:%S'
        self.theme = 'light'
        self.last_cleanup = None
        
        # Initialize default settings (will be overridden by load_settings)
        self.check_interval = 60
        self.timeout = 5
        self.expected_status = 200
        self.ssl_check_interval = 3600  # 1 hour in seconds
        self.performance_threshold = 1000
        self.consecutive_checks_needed = 2
        self.smtp_server = ''
        self.smtp_port = 587
        self.smtp_security = 'TLS'
        self.smtp_user = ''
        self.smtp_pass = ''
        self.recipient_email = ''
        self.from_name = ''
        self.subject_prefix = 'PingDaddyPro:'
        self.email_events = ['online', 'offline', 'content_error', 'performance', 'ssl_expire']
        
        # Load settings from database
        self.load_settings()
        self.load_webhooks()
        self.load_websites()
        
    def load_settings(self):
        try:
            cursor, conn = get_db_cursor()
            cursor.execute('SELECT * FROM settings WHERE id=1')
            settings = cursor.fetchone()
            conn.close()
            
            if settings:
                self.check_interval = settings['check_interval'] or 60
                self.timeout = settings['timeout'] or 5
                self.expected_status = settings['expected_status'] or 200
                self.performance_threshold = settings['performance_threshold'] or 1000
                self.consecutive_checks_needed = settings['consecutive_checks'] or 2
                self.smtp_server = settings['smtp_server'] or ''
                self.smtp_port = settings['smtp_port'] or 587
                self.smtp_security = settings['smtp_security'] or 'TLS'
                self.smtp_user = settings['smtp_user'] or ''
                self.smtp_pass = settings['smtp_pass'] or ''
                self.recipient_email = settings['recipient_email'] or ''
                self.from_name = settings['from_name'] or ''
                self.subject_prefix = settings['subject_prefix'] or 'PingDaddyPro:'
                self.notification_method = settings['notification_method'] or 'both'
                self.user_timezone = settings['timezone'] or 'UTC'
                self.time_format = settings['time_format'] or '%Y-%m-%d %H:%M:%S'
                self.theme = settings['theme'] or 'light'
                self.ssl_check_interval = settings.get('ssl_check_interval', 3600) or 3600
                email_events_str = settings['email_events'] if settings['email_events'] else '["online","offline","content_error","performance","ssl_expire"]'
                try:
                    # Try to parse as JSON first
                    self.email_events = json.loads(email_events_str)
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, treat as comma-separated string
                    self.email_events = email_events_str.split(',') if email_events_str else ['online', 'offline', 'content_error', 'performance', 'ssl_expire']
                print("Settings loaded successfully")
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            traceback.print_exc()
    
    def save_settings(self, settings):
        try:
            # Debug: Print email_events value
            print(f"DEBUG: email_events received: {settings.get('email_events', 'NOT_FOUND')}")
            print(f"DEBUG: email_events type: {type(settings.get('email_events', 'NOT_FOUND'))}")
            
            # Ensure email_events exists with default value
            if 'email_events' not in settings:
                settings['email_events'] = '["Back Online", "Offline", "Content Error", "Performance", "SSL Expiration"]'
            
            cursor, conn = get_db_cursor()
            
            # Check if ssl_check_interval column exists
            cursor.execute('''SELECT column_name FROM information_schema.columns 
                             WHERE table_name='settings' AND column_name='ssl_check_interval' ''')
            ssl_column_exists = cursor.fetchone() is not None
            
            print(f"DEBUG: ssl_check_interval value: {settings.get('ssl_check_interval', 'NOT_FOUND')}")
            print(f"DEBUG: ssl_column_exists: {ssl_column_exists}")
            
            if ssl_column_exists:
                cursor.execute('''UPDATE settings SET 
                                 check_interval=%s, timeout=%s, expected_status=%s, performance_threshold=%s, consecutive_checks=%s,
                                 smtp_server=%s, smtp_port=%s, smtp_security=%s, smtp_user=%s, smtp_pass=%s, recipient_email=%s,
                                 from_name=%s, subject_prefix=%s, notification_method=%s, timezone=%s, time_format=%s, theme=%s, email_events=%s, ssl_check_interval=%s WHERE id=1''', 
                             (settings['check_interval'], settings['timeout'], settings['expected_status'], 
                              settings['performance_threshold'], settings['consecutive_checks'],
                              settings['smtp_server'], settings['smtp_port'], settings['smtp_security'],
                              settings['smtp_user'], settings['smtp_pass'], settings['recipient_email'],
                              settings['from_name'], settings['subject_prefix'], settings['notification_method'],
                              settings['timezone'], settings['time_format'], settings['theme'], settings['email_events'],
                              settings.get('ssl_check_interval', 3600)))
            else:
                cursor.execute('''UPDATE settings SET 
                                 check_interval=%s, timeout=%s, expected_status=%s, performance_threshold=%s, consecutive_checks=%s,
                                 smtp_server=%s, smtp_port=%s, smtp_security=%s, smtp_user=%s, smtp_pass=%s, recipient_email=%s,
                                 from_name=%s, subject_prefix=%s, notification_method=%s, timezone=%s, time_format=%s, theme=%s, email_events=%s WHERE id=1''', 
                             (settings['check_interval'], settings['timeout'], settings['expected_status'], 
                              settings['performance_threshold'], settings['consecutive_checks'],
                              settings['smtp_server'], settings['smtp_port'], settings['smtp_security'],
                              settings['smtp_user'], settings['smtp_pass'], settings['recipient_email'],
                              settings['from_name'], settings['subject_prefix'], settings['notification_method'],
                              settings['timezone'], settings['time_format'], settings['theme'], settings['email_events']))
            
            conn.commit()
            conn.close()
            self.load_settings()
            print("Settings saved successfully")
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            traceback.print_exc()
            return False
    def test_smtp_settings(self, settings):
        """Test SMTP connection with provided settings"""
        try:
            if not all([settings['smtp_server'], settings['smtp_port'], 
                       settings['smtp_user'], settings['smtp_pass']]):
                return False, "Please fill all required SMTP settings"
                
            recipient = settings['recipient_email'] or settings['smtp_user']
            if not recipient:
                return False, "Please set either recipient email or use sender email as recipient"
                
            # Create message
            msg = MIMEMultipart()
            from_name = settings['from_name'] or settings['smtp_user']
            msg['From'] = f"{from_name} <{settings['smtp_user']}>"
            msg['To'] = recipient
            msg['Subject'] = f"{settings['subject_prefix']} SMTP Test"
            
            body = "This is a test email from Ping Daddy to verify SMTP settings are working correctly."
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            if settings['smtp_security'] == "SSL":
                server = smtplib.SMTP_SSL(settings['smtp_server'], int(settings['smtp_port']))
            else:
                server = smtplib.SMTP(settings['smtp_server'], int(settings['smtp_port']))
                
            if settings['smtp_security'] == "TLS":
                server.starttls()
                
            server.login(settings['smtp_user'], settings['smtp_pass'])
            
            # Send test email
            server.sendmail(settings['smtp_user'], recipient, msg.as_string())
            server.quit()
            
            return True, f"SMTP test successful! Test email sent to {recipient}"
            
        except Exception as e:
            return False, f"SMTP test failed: {str(e)}"
        
    def format_timestamp(self, dt):
        """Format datetime according to user's timezone and format preferences"""
        try:
            # Convert to user's timezone
            user_tz = pytz_timezone(self.user_timezone)
            if dt.tzinfo is None:
                # If datetime is naive, assume UTC
                dt = pytz.UTC.localize(dt)
            localized_dt = dt.astimezone(user_tz)
            return localized_dt.strftime(self.time_format)
        except Exception as e:
            print(f"Error formatting timestamp: {str(e)}")
            # Fallback to default format
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def load_webhooks(self):
        try:
            cursor, conn = get_db_cursor()
            cursor.execute('SELECT * FROM webhooks')
            webhooks = cursor.fetchall()
            conn.close()
            
            print(f"Loading webhooks from database: {len(webhooks)} webhooks found")
            for i, webhook in enumerate(webhooks):
                print(f"Webhook {i+1}: {webhook}")
            
            self.webhooks = []
            for webhook in webhooks:
                # Parse events properly - handle empty strings and None values
                events_str = webhook['events'] if webhook['events'] else ''
                events = [event.strip() for event in events_str.split(',') if event.strip()] if events_str else []
                
                webhook_data = {
                    'id': webhook['id'],
                    'name': webhook['name'],
                    'url': webhook['url'],
                    'secret': webhook['secret'],
                    'events': events,
                    'active': bool(webhook['active'])
                }
                self.webhooks.append(webhook_data)
                print(f"Loaded webhook: {webhook['name']} with events: {events}")
            print(f"Webhooks loaded successfully - Total in memory: {len(self.webhooks)}")
        except Exception as e:
            print(f"Error loading webhooks: {str(e)}")
            traceback.print_exc()
    
    def save_webhook(self, webhook_data):
        try:
            # Validate required fields
            if not webhook_data.get('name') or not webhook_data.get('url'):
                return False
            
            # Ensure events is a list
            if 'events' not in webhook_data or not isinstance(webhook_data['events'], list):
                webhook_data['events'] = []
            
            cursor, conn = get_db_cursor()
            
            events_str = ','.join(webhook_data['events']) if webhook_data['events'] else ''
            print(f"Saving webhook: {webhook_data['name']} with events: {webhook_data['events']} -> events_str: '{events_str}'")
            
            # Prepare data
            name = webhook_data['name']
            url = webhook_data['url']
            secret = webhook_data.get('secret', '')
            active = webhook_data.get('active', True)
            
            if 'id' in webhook_data and webhook_data['id'] and webhook_data['id'] != '':
                cursor.execute('''UPDATE webhooks SET name=%s, url=%s, secret=%s, events=%s, active=%s
                             WHERE id=%s''', 
                             (name, url, secret, events_str, active, webhook_data['id']))
                print(f"DEBUG: Updated webhook with ID {webhook_data['id']}")
            else:
                cursor.execute('''INSERT INTO webhooks (name, url, secret, events, active)
                             VALUES (%s, %s, %s, %s, %s)''', 
                             (name, url, secret, events_str, active))
                print(f"DEBUG: Inserted new webhook")
            
            conn.commit()
            print(f"DEBUG: Committed webhook to database")
            
            # Verify the webhook was saved
            cursor.execute('SELECT COUNT(*) FROM webhooks')
            count_result = cursor.fetchone()
            count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            print(f"DEBUG: Total webhooks in database after save: {count}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving webhook: {str(e)}")
            traceback.print_exc()
            return False
    
    def save_webhooks_bulk_direct(self, webhooks_data):
        """Save multiple webhooks directly to database"""
        try:
            cursor, conn = get_db_cursor()
            
            # Clear existing webhooks
            cursor.execute('DELETE FROM webhooks')
            print("DEBUG: Cleared existing webhooks")
            
            # Insert new webhooks
            for i, webhook_data in enumerate(webhooks_data):
                events_str = ','.join(webhook_data['events']) if webhook_data['events'] else ''
                cursor.execute('''INSERT INTO webhooks (name, url, secret, events, active)
                             VALUES (%s, %s, %s, %s, %s)''', 
                             (webhook_data['name'], webhook_data['url'], 
                              webhook_data.get('secret', ''), events_str, 
                              webhook_data.get('active', True)))
                print(f"DEBUG: Inserted webhook {i+1}: {webhook_data['name']}")
            
            conn.commit()
            print("DEBUG: Committed all webhooks to database")
            
            # Verify the webhooks were saved
            cursor.execute('SELECT COUNT(*) FROM webhooks')
            count_result = cursor.fetchone()
            count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            print(f"DEBUG: Total webhooks in database after bulk save: {count}")
            
            conn.close()
            
            # Reload webhooks into memory
            self.load_webhooks()
            print(f"DEBUG: Webhooks reloaded into memory: {len(self.webhooks)}")
            
            return True
        except Exception as e:
            print(f"Error saving webhooks bulk direct: {str(e)}")
            traceback.print_exc()
            return False
    
    def clear_all_webhooks(self):
        """Clear all webhooks from database"""
        try:
            cursor, conn = get_db_cursor()
            
            # Check how many webhooks exist before clearing
            cursor.execute('SELECT COUNT(*) FROM webhooks')
            count_result = cursor.fetchone()
            count_before = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            print(f"DEBUG: Webhooks in database before clearing: {count_before}")
            
            # Clear all webhooks
            cursor.execute('DELETE FROM webhooks')
            
            # Check how many webhooks exist after clearing
            cursor.execute('SELECT COUNT(*) FROM webhooks')
            count_result = cursor.fetchone()
            count_after = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            print(f"DEBUG: Webhooks in database after clearing: {count_after}")
            
            conn.commit()
            conn.close()
            
            print("All webhooks cleared successfully")
            return True
        except Exception as e:
            print(f"Error clearing webhooks: {str(e)}")
            traceback.print_exc()
            return False
    
    def delete_webhook(self, webhook_id):
        try:
            cursor, conn = get_db_cursor()
            cursor.execute('DELETE FROM webhooks WHERE id=%s', (webhook_id,))
            conn.commit()
            conn.close()
            print("Webhook deleted successfully")
            return True
        except Exception as e:
            print(f"Error deleting webhook: {str(e)}")
            traceback.print_exc()
            return False
    
    def load_websites(self):
        try:
            cursor, conn = get_db_cursor()
            cursor.execute('SELECT * FROM websites')
            websites = cursor.fetchall()
            conn.close()
            
            self.websites = []
            self.website_expected_texts = {}
            
            for website in websites:
                self.websites.append(website['url'])
                if website['expected_text']:
                    self.website_expected_texts[website['url']] = website['expected_text']
            print("Websites loaded successfully")
        except Exception as e:
            print(f"Error loading websites: {str(e)}")
            traceback.print_exc()
    
    def save_websites(self, websites_data):
        try:
            cursor, conn = get_db_cursor()
            
            # Clear existing websites
            cursor.execute('DELETE FROM websites')
            
            # Insert new websites
            for website in websites_data:
                if '|' in website:
                    parts = website.split('|', 1)
                    url = parts[0].strip()
                    expected_text = parts[1].strip()
                    cursor.execute('INSERT INTO websites (url, expected_text) VALUES (%s, %s)', (url, expected_text))
                else:
                    url = website.strip()
                    cursor.execute('INSERT INTO websites (url, expected_text) VALUES (%s, %s)', (url, None))
            
            conn.commit()
            conn.close()
            self.load_websites()
            print("Websites saved successfully")
            return True
        except Exception as e:
            print(f"Error saving websites: {str(e)}")
            traceback.print_exc()
            return False
    
    def add_to_history(self, website, status, response_time, details):
        try:
            cursor, conn = get_db_cursor()
            # Store timestamp in UTC using timezone-aware datetime
            timestamp = datetime.now(timezone.utc)
            cursor.execute('INSERT INTO history (timestamp, website, status, response_time, details) VALUES (%s, %s, %s, %s, %s)',
                      (timestamp, website, status, response_time, details))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error adding to history: {str(e)}")
            traceback.print_exc()
    
    def add_to_performance_data(self, website, status, response_time, details):
        try:
            cursor, conn = get_db_cursor()
            # Store timestamp in UTC using timezone-aware datetime
            timestamp = datetime.now(timezone.utc)
            cursor.execute('INSERT INTO performance_data (timestamp, website, status, response_time, details) VALUES (%s, %s, %s, %s, %s)',
                      (timestamp, website, status, response_time, details))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error adding to performance data: {str(e)}")
            traceback.print_exc()
    
    def cleanup_old_data(self, retention_days=90):
        """Clean up old data from performance_data and history tables"""
        try:
            cursor, conn = get_db_cursor()
            
            # Calculate cutoff date (90 days ago)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            # Clean up old performance data
            cursor.execute('DELETE FROM performance_data WHERE timestamp < %s', (cutoff_date,))
            perf_deleted = cursor.rowcount
            
            # Clean up old history data
            cursor.execute('DELETE FROM history WHERE timestamp < %s', (cutoff_date,))
            hist_deleted = cursor.rowcount
            
            # Clean up old SSL certificate data (keep only latest for each website)
            cursor.execute('''DELETE FROM ssl_certificates WHERE id NOT IN (
                SELECT MAX(id) FROM ssl_certificates GROUP BY website
            ) AND last_checked < %s''', (cutoff_date,))
            ssl_deleted = cursor.rowcount
            
            # Clean up old login attempts (keep only last 30 days for security monitoring)
            login_cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            cursor.execute('DELETE FROM login_attempts WHERE attempt_time < %s', (login_cutoff_date,))
            login_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if perf_deleted > 0 or hist_deleted > 0 or ssl_deleted > 0 or login_deleted > 0:
                print(f"Cleanup completed: {perf_deleted} performance records, {hist_deleted} history records, {ssl_deleted} SSL records, {login_deleted} login attempts deleted")
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            traceback.print_exc()
    
    def get_history(self, limit=50, offset=0, website_filter='', status_filter='', date_from='', date_to=''):
        try:
            cursor, conn = get_db_cursor()
            
            # Build query based on filters - use performance_data table for complete history
            query = 'SELECT * FROM performance_data'
            count_query = 'SELECT COUNT(*) FROM performance_data'
            params = []
            conditions = []
            
            if website_filter:
                conditions.append(' website = %s')
                params.append(website_filter)
                
            if status_filter:
                conditions.append(' status = %s')
                params.append(status_filter)
            
            # Add date range filtering
            if date_from:
                conditions.append(' DATE(timestamp) >= %s')
                params.append(date_from)
                
            if date_to:
                conditions.append(' DATE(timestamp) <= %s')
                params.append(date_to)
            
            if conditions:
                where_clause = ' WHERE ' + ' AND '.join(conditions)
                query += where_clause
                count_query += where_clause
            
            query += ' ORDER BY timestamp DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            # Get history data
            cursor.execute(query, params)
            history = cursor.fetchall()
            
            # Get total count for has_more calculation
            cursor.execute(count_query, params[:-2])  # Remove LIMIT and OFFSET params
            count_result = cursor.fetchone()
            total_count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            
            conn.close()
            
            history_list = []
            for item in history:
                # Parse timestamp and convert to user's timezone
                if isinstance(item['timestamp'], str):
                    timestamp_utc = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
                    timestamp_utc = pytz.UTC.localize(timestamp_utc)
                else:
                    timestamp_utc = item['timestamp']
                    if timestamp_utc.tzinfo is None:
                        timestamp_utc = pytz.UTC.localize(timestamp_utc)
                
                formatted_timestamp = self.format_timestamp(timestamp_utc)
                
                history_list.append({
                    'id': item['id'],
                    'timestamp': formatted_timestamp,
                    'website': item['website'],
                    'status': item['status'],
                    'response_time': item['response_time'],
                    'details': item['details']
                })
            
            # Calculate if there are more records
            has_more = (offset + limit) < total_count
            
            return {
                'history': history_list,
                'has_more': has_more,
                'total_count': total_count
            }
        except Exception as e:
            print(f"Error getting history: {str(e)}")
            traceback.print_exc()
            return {'history': [], 'has_more': False, 'total_count': 0}
    
    def get_performance_data(self, website, hours=24):
        try:
            cursor, conn = get_db_cursor()
            time_limit = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            cursor.execute('SELECT * FROM performance_data WHERE website=%s AND timestamp >= %s ORDER BY timestamp',
                      (website, time_limit))
            performance_data = cursor.fetchall()
            conn.close()
            
            timestamps = []
            response_times = []
            statuses = []
            
            for item in performance_data:
                if isinstance(item['timestamp'], str):
                    timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = item['timestamp']
                
                timestamps.append(timestamp)
                response_times.append(item['response_time'])
                statuses.append(item['status'])
            
            return timestamps, response_times, statuses
        except Exception as e:
            print(f"Error getting performance data: {str(e)}")
            traceback.print_exc()
            return [], [], []
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate for a website"""
        try:
            if not url.startswith('https://'):
                return None, "Not HTTPS", None
                
            domain = urlparse(url).netloc
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate
            with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    # Get issuer
                    issuer = dict(x[0] for x in cert['issuer'])
                    issuer_str = issuer.get('organizationName', 'Unknown')
                    
                    return {
                        'valid_from': not_before,
                        'valid_to': not_after,
                        'issuer': issuer_str,
                        'days_remaining': (not_after - datetime.now()).days
                    }, "Valid", None
                    
        except Exception as e:
            return None, f"SSL Error: {str(e)}", None
    
    def store_ssl_certificate_info(self, website, ssl_info):
        try:
            cursor, conn = get_db_cursor()
            
            # Check if record exists
            cursor.execute('SELECT id FROM ssl_certificates WHERE website=%s', (website,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''UPDATE ssl_certificates SET valid_from=%s, valid_to=%s, 
                           issuer=%s, last_checked=%s WHERE website=%s''',
                           (ssl_info['valid_from'], ssl_info['valid_to'], 
                            ssl_info['issuer'], datetime.now(), website))
            else:
                # Insert new record
                cursor.execute('''INSERT INTO ssl_certificates 
                           (website, valid_from, valid_to, issuer, last_checked)
                           VALUES (%s, %s, %s, %s, %s)''',
                           (website, ssl_info['valid_from'], ssl_info['valid_to'], 
                            ssl_info['issuer'], datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error storing SSL certificate info: {str(e)}")
            traceback.print_exc()
    
    def handle_ssl_expiration(self, website, ssl_info):
        """Handle SSL certificate expiration event"""
        notification_method = self.notification_method
        
        # Check if we've already sent a notification for this expiration
        if website in self.website_status:
            last_notification = self.website_status[website].get('ssl_notification_sent')
            if last_notification and (datetime.now() - last_notification).total_seconds() < 86400:  # 24 hours
                return  # Don't send notifications more than once per day
        
        days_remaining = ssl_info['days_remaining']
        expire_date = ssl_info['valid_to']
        
        # Add to history for tracking (like other notifications)
        self.add_to_history(website, "SSL Expiration", 0, 
                           f"SSL certificate expires in {days_remaining} days")
        
        # Send notifications based on method
        if notification_method in ['email', 'both']:
            self.send_ssl_expiration_email(website, days_remaining, expire_date)
            
        if notification_method in ['webhook', 'both']:
            self.send_webhook_for_event("ssl_expire", website, 0, 
                                       f"SSL certificate expires in {days_remaining} days",
                                       days_remaining, expire_date)
        
        # Record that we sent a notification
        if website in self.website_status:
            self.website_status[website]['ssl_notification_sent'] = datetime.now()
    
    def send_ssl_expiration_email(self, website, days_remaining, expire_date):
        """Send email notification about SSL certificate expiration"""
        if not self.smtp_server or not self.smtp_user or not self.smtp_pass:
            print("SMTP not configured")
            return False
            
        recipient = self.recipient_email or self.smtp_user
        
        try:
            msg = MIMEMultipart()
            from_name = self.from_name or self.smtp_user
            msg['From'] = f"{from_name} <{self.smtp_user}>"
            msg['To'] = recipient
            
            # Format timestamp
            current_time = self.format_timestamp(datetime.now())
            expire_time = self.format_timestamp(expire_date)
            
            subject = f"{self.subject_prefix} SSL Certificate Expiration Alert for {website}"
            body = f"""🚨 SSL Certificate Alert from Ping Daddy

Website: {website}
SSL Certificate is expiring soon!

Expiration Date: {expire_time}
Days Remaining: {days_remaining}
Current Time: {current_time}

Please renew the SSL certificate to avoid service disruption.

---
Ping Daddy - Professional Website Monitoring
"""
            
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            if self.smtp_security == "SSL":
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                
            if self.smtp_security == "TLS":
                server.starttls()
                
            server.login(self.smtp_user, self.smtp_pass)
            
            server.send_message(msg)
            server.quit()
            
            print(f"SSL expiration notification sent for {website}")
            return True
            
        except Exception as e:
            print(f"Error sending SSL expiration email: {str(e)}")
            traceback.print_exc()
            return False
    
    def check_website(self, url):
        try:
            # Extract expected text if specified
            expected_text = None
            if '|' in url:
                parts = url.split('|', 1)
                url = parts[0].strip()
                expected_text = parts[1].strip()
            else:
                expected_text = self.website_expected_texts.get(url)
            
            # Check DNS resolution first
            try:
                domain = urlparse(url).netloc
                dns.resolver.resolve(domain, 'A')
            except Exception as e:
                return "DNS Error", 0, f"DNS Resolution Failed: {str(e)}", None
            
            start_time = time.time()
            
            # Set headers to simulate a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make the request
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
                response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            except requests.exceptions.Timeout:
                return "Timeout Error", int((time.time() - start_time) * 1000), f"Request timed out after {self.timeout} seconds", None
            except requests.exceptions.RequestException as e:
                return "Connection Error", int((time.time() - start_time) * 1000), f"Connection failed: {str(e)}", None
            
            # Check SSL certificate for HTTPS sites (only if interval has passed)
            ssl_info = None
            ssl_status = "N/A"
            current_time = time.time()
            
            if url.startswith('https://'):
                # Check if we need to verify SSL certificate
                last_ssl_check = self.ssl_last_check_times.get(url, 0)
                print(f"DEBUG SSL: {url} - last_ssl_check: {last_ssl_check}, current_time: {current_time}, interval: {self.ssl_check_interval}")
                if current_time - last_ssl_check >= self.ssl_check_interval:
                    print(f"DEBUG SSL: Running SSL check for {url}")
                    ssl_info, ssl_status, _ = self.check_ssl_certificate(url)
                    self.ssl_last_check_times[url] = current_time
                    print(f"DEBUG SSL: SSL check completed for {url}, status: {ssl_status}")
                    
                    # Check for SSL errors
                    if ssl_status == "Invalid":
                        return "SSL Error", response_time, f"SSL Certificate Error: {ssl_status}", None
                    
                    # Store SSL certificate info
                    if ssl_info:
                        self.store_ssl_certificate_info(url, ssl_info)
                        
                    # Check for expiration within 48 hours
                    if ssl_info and ssl_info['days_remaining'] <= 2:  # 2 days = 48 hours
                        self.handle_ssl_expiration(url, ssl_info)
                        
                    # Emit SSL update via WebSocket
                    if ssl_info:
                        socketio.emit('ssl_update', {
                            'website': url,
                            'ssl_info': ssl_info,
                            'ssl_status': ssl_status
                        })
                else:
                    # Use cached SSL info if available
                    cached_ssl_info = self.get_ssl_info(url)
                    if cached_ssl_info:
                        ssl_info = cached_ssl_info
                        ssl_status = "Valid" if cached_ssl_info.get('days_remaining', 0) > 0 else "Expired"
            
            # Check status code
            if response.status_code != self.expected_status:
                return "Status Error", response_time, f"Status Code: {response.status_code}, Expected: {self.expected_status}", None
            
            # Check for expected text if specified
            if expected_text and expected_text not in response.text:
                return "Content Error", response_time, f"Expected text '{expected_text}' not found in response", expected_text
            
            # Check performance threshold
            if response_time > self.performance_threshold:
                return "Performance Issue", response_time, f"Response time {response_time}ms exceeds threshold {self.performance_threshold}ms", None
            
            # Details without SSL status (SSL is shown separately in frontend)
            details = f"Status Code: {response.status_code}"
                
            return "Online", response_time, details, expected_text
            
        except requests.exceptions.Timeout:
            return "Timeout", 0, "Request timed out", None
        except requests.exceptions.ConnectionError:
            return "Connection Error", 0, "Connection failed", None
        except requests.exceptions.RequestException as e:
            return "Error", 0, f"Request failed: {str(e)}", None
        except Exception as e:
            return "Error", 0, f"Unexpected error: {str(e)}", None
    
    def send_email_notification(self, website, status, response_time, details):
        """Send email notification for website status change"""
        if not self.smtp_server or not self.smtp_user or not self.smtp_pass:
            print("SMTP not configured")
            return False
            
        recipient = self.recipient_email or self.smtp_user
        
        try:
            msg = MIMEMultipart()
            from_name = self.from_name or self.smtp_user
            msg['From'] = f"{from_name} <{self.smtp_user}>"
            msg['To'] = recipient
            
            # Format timestamp
            current_time = self.format_timestamp(datetime.now())
            
            subject = f"{self.subject_prefix} {status} - {website}"
            body = f"""🚨 Website Monitoring Alert from Ping Daddy

Website: {website}
Status: {status}
Response Time: {response_time}ms
Details: {details}
Time: {current_time}

Please check the website for issues.

---
Ping Daddy - Professional Website Monitoring
"""
            
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            if self.smtp_security == "SSL":
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                
            if self.smtp_security == "TLS":
                server.starttls()
                
            server.login(self.smtp_user, self.smtp_pass)
            
            server.send_message(msg)
            server.quit()
            
            print(f"Email notification sent for {website}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            traceback.print_exc()
            return False
    
    def send_webhook_for_event(self, event_type, website, response_time, details, days_remaining=None, expire_date=None):
        """Send webhook notification for events"""
        for webhook in self.webhooks:
            if not webhook['active']:
                continue
                
            # Check if webhook should receive this event
            should_send = False
            if event_type in webhook['events']:
                should_send = True
            elif event_type == 'Online' and 'online' in webhook['events']:
                should_send = True
            elif event_type in ['Content Error', 'DNS Error', 'Timeout Error', 'SSL Error', 'Connection Error', 'Status Error'] and 'offline' in webhook['events']:
                should_send = True
            elif event_type == 'Content Error' and 'content_error' in webhook['events']:
                should_send = True
            elif event_type == 'Performance' and 'performance' in webhook['events']:
                should_send = True
            elif event_type == 'ssl_expire' and 'ssl_expire' in webhook['events']:
                should_send = True
                
            if not should_send:
                continue
                
            try:
                # Format timestamp without microseconds and timezone
                timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
                
                payload = {
                    'event': event_type,
                    'website': website,
                    'timestamp': timestamp,
                    'response_time': response_time,
                    'details': details,
                    'monitor_id': 'website_monitor'
                }
                
                # Add SSL-specific data
                if event_type == "ssl_expire":
                    payload.update({
                        'days_remaining': days_remaining,
                        'expiration_date': expire_date.isoformat() if expire_date else None
                    })
                
                # Sign the payload if secret is provided
                if webhook['secret']:
                    signature = hmac.new(
                        webhook['secret'].encode(),
                        json.dumps(payload).encode(),
                        hashlib.sha256
                    ).hexdigest()
                    headers = {
                        'X-Webhook-Signature': signature,
                        'Content-Type': 'application/json'
                    }
                else:
                    headers = {'Content-Type': 'application/json'}
                
                response = requests.post(webhook['url'], json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print(f"Webhook sent successfully to {webhook['name']}")
                else:
                    print(f"Webhook failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"Error sending webhook {webhook['name']}: {str(e)}")
                traceback.print_exc()
    
    def monitor_websites(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            # Run cleanup once per day (at midnight or first run)
            current_time = datetime.now()
            if (self.last_cleanup is None or 
                (current_time - self.last_cleanup).total_seconds() >= 86400):  # 24 hours
                self.cleanup_old_data()
                self.last_cleanup = current_time
            
            for website in self.websites:
                try:
                    status, response_time, details, expected_text = self.check_website(website)
                    
                    # Store in performance data
                    self.add_to_performance_data(website, status, response_time, details)
                    
                    # Check if status changed
                    if website not in self.website_status:
                        current_time = datetime.now()
                        self.website_status[website] = {
                            'status': status,
                            'response_time': response_time,
                            'details': details,
                            'last_check': current_time,
                            'consecutive_failures': 0,
                            'last_notification_status': None
                        }
                        self.add_to_history(website, status, response_time, details)
                    else:
                        previous_status = self.website_status[website]['status']
                        current_time = datetime.now()
                        
                        # Update website status
                        self.website_status[website].update({
                            'status': status,
                            'response_time': response_time,
                            'details': details,
                            'last_check': current_time
                        })
                        
                        # Track consecutive failures for status changes
                        if status != "Online":
                            self.website_status[website]['consecutive_failures'] += 1
                        else:
                            self.website_status[website]['consecutive_failures'] = 0
                        
                        print(f"DEBUG: {website} - Status: {status}, Previous: {previous_status}, Consecutive failures: {self.website_status[website]['consecutive_failures']}, Needed: {self.consecutive_checks_needed}")
                        
                        # Trigger notifications when:
                        # 1. Status changes AND consecutive failures >= consecutive_checks_needed, OR
                        # 2. First time reaching error status AND consecutive failures >= consecutive_checks_needed, OR
                        # 3. Consecutive failures reaches the threshold (for persistent errors), OR
                        # 4. Website recovers to Online status (from any error status)
                        should_notify = False
                        
                        if status != previous_status and self.website_status[website]['consecutive_failures'] >= self.consecutive_checks_needed:
                            should_notify = True
                            print(f"DEBUG: Condition 1 met for {website} - Status changed")
                        elif (status != "Online" and 
                              self.website_status[website]['consecutive_failures'] >= self.consecutive_checks_needed and 
                              previous_status == "Online"):
                            should_notify = True
                            print(f"DEBUG: Condition 2 met for {website} - First error")
                        elif (status != "Online" and 
                              self.website_status[website]['consecutive_failures'] == self.consecutive_checks_needed and
                              self.website_status[website].get('last_notification_status') != status):
                            should_notify = True
                            print(f"DEBUG: Condition 3 met for {website} - Reached threshold")
                        elif (status == "Online" and previous_status != "Online"):
                            should_notify = True
                            print(f"DEBUG: Condition 4 met for {website} - Recovered to Online")
                        
                        if should_notify:
                            print(f"DEBUG: Sending notification for {website} - Status: {status}, Previous: {previous_status}, Consecutive failures: {self.website_status[website]['consecutive_failures']}, Needed: {self.consecutive_checks_needed}")
                            
                            # Create custom message for Content Error recovery
                            notification_details = details
                            if (status == "Online" and previous_status == "Content Error" and expected_text):
                                notification_details = f"Expected text '{expected_text}' is back"
                            
                            self.add_to_history(website, status, response_time, notification_details)
                            
                            # Send notifications based on method
                            notification_method = self.notification_method
                            
                            if notification_method in ['email', 'both']:
                                # Check if this event should trigger email notification
                                should_send_email = False
                                if status == 'Online' and 'online' in self.email_events:
                                    should_send_email = True
                                elif status in ['Content Error', 'DNS Error', 'Timeout Error', 'SSL Error', 'Connection Error', 'Status Error'] and 'offline' in self.email_events:
                                    should_send_email = True
                                elif status == 'Content Error' and 'content_error' in self.email_events:
                                    should_send_email = True
                                elif status == 'Performance Issue' and 'performance' in self.email_events:
                                    should_send_email = True
                                elif status == 'SSL Expiration' and 'ssl_expire' in self.email_events:
                                    should_send_email = True
                                
                                if should_send_email:
                                    self.send_email_notification(website, status, response_time, notification_details)
                                
                            if notification_method in ['webhook', 'both']:
                                print(f"DEBUG: Sending webhook for {website}")
                                self.send_webhook_for_event(status, website, response_time, notification_details)
                            
                            # Update last notification status to prevent duplicates
                            self.website_status[website]['last_notification_status'] = status
                    
                    # Store response time for performance tracking
                    if website not in self.response_times:
                        self.response_times[website] = []
                    self.response_times[website].append(response_time)
                    
                    # Keep only last 100 response times
                    if len(self.response_times[website]) > 100:
                        self.response_times[website] = self.response_times[website][-100:]
                    
                except Exception as e:
                    print(f"Error monitoring {website}: {str(e)}")
                    traceback.print_exc()
            
            # Send WebSocket update after each monitoring cycle
            try:
                socketio.emit('status_update', self.get_status())
            except Exception as e:
                print(f"Error sending WebSocket update: {str(e)}")
            
            # Sleep for the check interval
            time.sleep(self.check_interval)
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_websites)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("Monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.is_monitoring = False
        print("Monitoring stopped")
    
    def get_status(self):
        """Get current status of all websites"""
        status_list = []
        for website in self.websites:
            if website in self.website_status:
                status = self.website_status[website]
                status_list.append({
                    'url': website,
                    'status': status['status'],
                    'response_time': status['response_time'],
                    'details': status['details'],
                    'last_check': self.format_timestamp(status['last_check'])
                })
            else:
                status_list.append({
                    'url': website,
                    'status': 'Not checked yet',
                    'response_time': 0,
                    'details': 'Waiting for first check',
                    'last_check': 'N/A'
                })
        return status_list
    
    def get_available_timezones(self):
        """Get list of all available timezones"""
        import pytz
        return sorted(pytz.all_timezones)
    
    def get_ssl_info(self, website):
        """Get SSL certificate information for a website"""
        try:
            cursor, conn = get_db_cursor()
            cursor.execute('SELECT * FROM ssl_certificates WHERE website=%s ORDER BY last_checked DESC LIMIT 1', (website,))
            ssl_data = cursor.fetchone()
            conn.close()
            
            if ssl_data:
                valid_to = ssl_data['valid_to']
                valid_from = ssl_data['valid_from']
                last_checked = ssl_data['last_checked']
                issuer = ssl_data['issuer']
                website_name = ssl_data['website']
                
                # Parse datetime if it's a string
                if isinstance(valid_to, str):
                    try:
                        valid_to = dateutil_parser.parse(valid_to)
                    except:
                        valid_to = None
                
                if isinstance(valid_from, str):
                    try:
                        valid_from = dateutil_parser.parse(valid_from)
                    except:
                        valid_from = None
                
                if isinstance(last_checked, str):
                    try:
                        last_checked = dateutil_parser.parse(last_checked)
                    except:
                        last_checked = None
                
                # Calculate days remaining
                days_remaining = None
                if valid_to:
                    try:
                        # Ensure both are timezone-aware
                        if valid_to.tzinfo is None:
                            valid_to = pytz.UTC.localize(valid_to)
                        now = datetime.now(pytz.UTC)
                        days_remaining = (valid_to - now).days
                    except Exception as e:
                        print(f"Error calculating days remaining: {e}")
                        days_remaining = None
                
                # Convert datetime objects to ISO strings for JSON serialization
                def safe_isoformat(dt):
                    if dt is None:
                        return None
                    try:
                        if hasattr(dt, 'isoformat'):
                            return dt.isoformat()
                        return str(dt)
                    except:
                        return str(dt)
                
                return {
                    'website': website_name,
                    'valid_from': safe_isoformat(valid_from),
                    'valid_to': safe_isoformat(valid_to),
                    'issuer': issuer,
                    'last_checked': safe_isoformat(last_checked),
                    'days_remaining': days_remaining
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error getting SSL info: {str(e)}")
            traceback.print_exc()
            return None

# Create monitor instance
monitor = WebsiteMonitor()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    # Send initial status when client connects
    emit('status_update', monitor.get_status())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    emit('status_update', monitor.get_status())

@socketio.on('request_ssl_info')
def handle_ssl_request():
    """Handle SSL info request from client"""
    print(f"DEBUG: SSL info request received, websites: {monitor.websites}")
    ssl_data = {}
    for website in monitor.websites:
        if website.startswith('https://'):
            print(f"DEBUG: Getting SSL info for {website}")
            ssl_info = monitor.get_ssl_info(website)
            if ssl_info:
                ssl_data[website] = ssl_info
                print(f"DEBUG: SSL info for {website}: {ssl_info}")
            else:
                print(f"DEBUG: No SSL info found for {website}")
    print(f"DEBUG: Emitting ssl_data: {ssl_data}")
    emit('ssl_data', ssl_data)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    return jsonify(monitor.get_status())

@app.route('/api/version')
def api_version():
    return jsonify({
        'version': APP_VERSION, 
        'name': 'PingDaddyPro',
        'build_date': BUILD_DATE,
        'git_commit': GIT_COMMIT,
        'full_version': f"{APP_VERSION} ({BUILD_DATE})"
    })

@app.route('/api/start', methods=['POST'])
@require_auth
def api_start():
    monitor.start_monitoring()
    return jsonify({'success': True, 'message': 'Monitoring started'})

@app.route('/api/stop', methods=['POST'])
@require_auth
def api_stop():
    monitor.stop_monitoring()
    return jsonify({'success': True, 'message': 'Monitoring stopped'})

@app.route('/api/login', methods=['POST'])
def api_login():
    """Login endpoint with brute force protection"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Get real client IP address
        ip_address = get_client_ip()
        
        print(f"DEBUG LOGIN: Username={username}, IP={ip_address}")
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        # Check if account is locked
        locked = is_account_locked(username, ip_address)
        print(f"DEBUG LOGIN: Account locked check result: {locked}")
        
        if locked:
            print(f"DEBUG LOGIN: Account {username} is locked!")
            return jsonify({'success': False, 'message': 'Account temporarily locked due to multiple failed attempts. Please try again in 15 minutes.'})
        
        login_result = login_user(username, password, ip_address)
        print(f"DEBUG LOGIN: Login result: {login_result}")
        
        if login_result:
            session['authenticated'] = True
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
    except Exception as e:
        print(f"Login API error: {str(e)}")
        return jsonify({'success': False, 'message': 'Login failed'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/change-password', methods=['POST'])
@require_auth
def api_change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'})
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'New password must be at least 8 characters long'})
        
        username = session.get('username')
        if not username:
            return jsonify({'success': False, 'message': 'User not authenticated'})
        
        # Verify current password
        cursor, conn = get_db_cursor()
        cursor.execute('SELECT password_hash FROM admin_users WHERE username = %s', (username,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'})
        
        if not verify_password(current_password, result['password_hash']):
            conn.close()
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        # Update password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('UPDATE admin_users SET password_hash = %s WHERE username = %s', (new_password_hash, username))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'})

@app.route('/api/auth-status', methods=['GET'])
def api_auth_status():
    """Check authentication status"""
    return jsonify({
        'authenticated': session.get('authenticated', False),
        'username': session.get('username', '')
    })

@app.route('/api/settings', methods=['GET', 'POST'])
@require_auth
def api_settings():
    if request.method == 'GET':
        return jsonify({
            'check_interval': monitor.check_interval,
            'timeout': monitor.timeout,
            'expected_status': monitor.expected_status,
            'performance_threshold': monitor.performance_threshold,
            'consecutive_checks': monitor.consecutive_checks_needed,
            'smtp_server': monitor.smtp_server,
            'smtp_port': monitor.smtp_port,
            'smtp_security': monitor.smtp_security,
            'smtp_user': monitor.smtp_user,
            'smtp_pass': monitor.smtp_pass,
            'recipient_email': monitor.recipient_email,
            'from_name': monitor.from_name,
            'subject_prefix': monitor.subject_prefix,
            'notification_method': monitor.notification_method,
            'timezone': monitor.user_timezone,
            'time_format': monitor.time_format,
            'theme': monitor.theme,
            'email_events': monitor.email_events,
            'ssl_check_interval': monitor.ssl_check_interval
        })
    else:
        data = request.json
        if monitor.save_settings(data):
            return jsonify({'success': True, 'message': 'Settings saved'})
        else:
            return jsonify({'success': False, 'message': 'Error saving settings'})

@app.route('/api/timezones')
def api_timezones():
    """Get list of all available timezones"""
    return jsonify({'timezones': monitor.get_available_timezones()})

@app.route('/api/websites', methods=['GET', 'POST'])
@require_auth
def api_websites():
    if request.method == 'GET':
        websites_with_text = []
        for website in monitor.websites:
            expected_text = monitor.website_expected_texts.get(website, '')
            if expected_text:
                websites_with_text.append(f"{website}|{expected_text}")
            else:
                websites_with_text.append(website)
        return jsonify({'websites': websites_with_text})
    else:
        data = request.json
        if monitor.save_websites(data.get('websites', [])):
            return jsonify({'success': True, 'message': 'Websites saved'})
        else:
            return jsonify({'success': False, 'message': 'Error saving websites'})

@app.route('/api/webhooks', methods=['GET'])
@require_auth
def api_get_webhooks():
    return jsonify({'webhooks': monitor.webhooks})

@app.route('/api/webhooks', methods=['POST'])
@require_auth
def api_save_webhook():
    try:
        data = request.json
        print(f"DEBUG: Received webhook data: {data}")
        
        # Validate required fields
        if not data.get('name') or not data.get('url'):
            print("DEBUG: Missing required fields")
            return jsonify({'success': False, 'message': 'Name and URL are required'})
        
        # Validate URL format
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(data['url'])
            if not parsed_url.scheme or not parsed_url.netloc:
                print("DEBUG: Invalid URL format")
                return jsonify({'success': False, 'message': 'Invalid URL format'})
        except:
            print("DEBUG: URL parsing failed")
            return jsonify({'success': False, 'message': 'Invalid URL format'})
        
        # Ensure events is a list
        if 'events' not in data or not isinstance(data['events'], list):
            data['events'] = []
        
        print(f"DEBUG: About to save webhook: {data}")
        if monitor.save_webhook(data):
            print("DEBUG: Webhook saved successfully, reloading...")
            monitor.load_webhooks()  # Reload webhooks after saving
            print(f"DEBUG: Webhooks reloaded - Total in memory: {len(monitor.webhooks)}")
            return jsonify({'success': True, 'message': 'Webhook saved'})
        else:
            print("DEBUG: Failed to save webhook")
            return jsonify({'success': False, 'message': 'Error saving webhook'})
    except Exception as e:
        print(f"DEBUG: Exception in api_save_webhook: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error saving webhook: {str(e)}'})

@app.route('/api/webhooks/bulk', methods=['POST'])
@require_auth
def api_save_webhooks_bulk():
    """Save multiple webhooks at once"""
    try:
        data = request.json
        webhooks = data.get('webhooks', [])
        
        print(f"Bulk webhooks import - received data: {data}")
        print(f"Bulk webhooks import - webhooks list: {webhooks}")
        print(f"Bulk webhooks import - webhooks count: {len(webhooks)}")
        
        if not isinstance(webhooks, list):
            return jsonify({'success': False, 'message': 'Webhooks must be a list'})
        
        # Use direct database approach
        print("DEBUG: Using direct database approach...")
        if monitor.save_webhooks_bulk_direct(webhooks):
            print("DEBUG: Bulk webhooks saved successfully")
            return jsonify({'success': True, 'message': f'{len(webhooks)} webhooks saved successfully'})
        else:
            print("DEBUG: Failed to save webhooks bulk")
            return jsonify({'success': False, 'message': 'Error saving webhooks'})
        
    except Exception as e:
        print(f"Error saving webhooks bulk: {str(e)}")
        return jsonify({'success': False, 'message': f'Error saving webhooks: {str(e)}'})

@app.route('/api/webhooks/<int:webhook_id>', methods=['DELETE'])
@require_auth
def api_delete_webhook(webhook_id):
    if monitor.delete_webhook(webhook_id):
        monitor.load_webhooks()  # Reload webhooks after deletion
        return jsonify({'success': True, 'message': 'Webhook deleted'})
    else:
        return jsonify({'success': False, 'message': 'Error deleting webhook'})

@app.route('/api/webhook/test', methods=['POST'])
@require_auth
def api_test_webhook():
    """Send a test webhook notification"""
    try:
        data = request.get_json()
        webhook_id = data.get('webhook_id')
        status = data.get('status')
        website = data.get('website')
        response_time = data.get('response_time', 0)
        details = data.get('details', '')
        
        if not webhook_id or not status or not website:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Get webhook details
        cursor, conn = get_db_cursor()
        cursor.execute('SELECT * FROM webhooks WHERE id = %s', (webhook_id,))
        webhook_row = cursor.fetchone()
        conn.close()
        
        if not webhook_row:
            return jsonify({'success': False, 'message': 'Webhook not found'})
        
        # Create temporary webhook object for testing
        test_webhook = {
            'id': webhook_row['id'],
            'name': webhook_row['name'],
            'url': webhook_row['url'],
            'secret': webhook_row['secret'],
            'events': webhook_row['events'].split(',') if webhook_row['events'] else [],
            'active': bool(webhook_row['active'])
        }
        
        # Send test webhook using the same logic as the main function
        try:
            import hmac
            import hashlib
            import json
            from datetime import datetime, timezone
            
            # Format timestamp without microseconds and timezone
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
            
            payload = {
                'event': status,
                'website': website,
                'timestamp': timestamp,
                'response_time': response_time,
                'details': details,
                'monitor_id': 'website_monitor',
                'test': True  # Mark as test notification
            }
            
            # Sign the payload if secret is provided
            if test_webhook['secret']:
                signature = hmac.new(
                    test_webhook['secret'].encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers = {
                    'X-Webhook-Signature': signature,
                    'Content-Type': 'application/json'
                }
            else:
                headers = {'Content-Type': 'application/json'}
            
            response = requests.post(test_webhook['url'], json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return jsonify({'success': True, 'message': 'Test webhook sent successfully'})
            else:
                return jsonify({'success': False, 'message': f'Webhook failed with status {response.status_code}'})
                
        except Exception as e:
            print(f"Error sending test webhook: {str(e)}")
            return jsonify({'success': False, 'message': f'Error sending webhook: {str(e)}'})
            
    except Exception as e:
        print(f"Error in test webhook API: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/history-statuses')
def api_history_statuses():
    """Get statuses that trigger notifications (from history table)"""
    try:
        # Get statuses that actually trigger notifications (from history table)
        cursor, conn = get_db_cursor()
        cursor.execute('SELECT DISTINCT status FROM history ORDER BY status')
        notification_statuses = [row['status'] for row in cursor.fetchall()]
        conn.close()
        
        # If no notification statuses exist yet, return common ones
        if not notification_statuses:
            notification_statuses = ["Online", "DNS Error", "Timeout Error", "Connection Error", 
                                    "SSL Error", "SSL Expiration", "Status Error", "Content Error", "Performance Issue"]
        
        # Always include SSL Expiration if it's not already there (since it's a special notification type)
        if "SSL Expiration" not in notification_statuses:
            notification_statuses.append("SSL Expiration")
        
        return jsonify({'statuses': notification_statuses})
    except Exception as e:
        print(f"Error getting history statuses: {str(e)}")
        return jsonify({'statuses': []})

@app.route('/api/history')
def api_history():
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    website_filter = request.args.get('website', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('dateFrom', '')
    date_to = request.args.get('dateTo', '')
    
    print(f"DEBUG: History API called - limit: {limit}, offset: {offset}, website_filter: '{website_filter}', status_filter: '{status_filter}', date_from: '{date_from}', date_to: '{date_to}'")
    
    history_data = monitor.get_history(limit, offset, website_filter, status_filter, date_from, date_to)
    
    print(f"DEBUG: History data returned - count: {len(history_data.get('history', []))}, has_more: {history_data.get('has_more', False)}")
    
    return jsonify(history_data)

@app.route('/api/history/export')
def api_history_export():
    """Export history data to CSV format"""
    website_filter = request.args.get('website', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('dateFrom', '')
    date_to = request.args.get('dateTo', '')
    
    print(f"DEBUG: History Export API called - website_filter: '{website_filter}', status_filter: '{status_filter}', date_from: '{date_from}', date_to: '{date_to}'")
    
    # Get all data (no limit/offset for export)
    history_data = monitor.get_history(999999, 0, website_filter, status_filter, date_from, date_to)
    
    # Create CSV content
    csv_content = "Timestamp,Website,Status,Response Time,Details\n"
    
    for record in history_data.get('history', []):
        # Escape CSV values properly
        timestamp = record['timestamp'].replace(',', ';')  # Replace comma with semicolon
        website = record['website'].replace(',', ';')
        status = record['status'].replace(',', ';')
        response_time = str(record['response_time'])
        details = record['details'].replace(',', ';').replace('\n', ' ').replace('\r', ' ')
        
        # Properly escape quotes and wrap in quotes if contains comma
        def escape_csv_field(field):
            if ',' in field or '"' in field or '\n' in field:
                return '"' + field.replace('"', '""') + '"'
            return field
        
        csv_content += f"{escape_csv_field(timestamp)},{escape_csv_field(website)},{escape_csv_field(status)},{escape_csv_field(response_time)},{escape_csv_field(details)}\n"
    
    # Create response with CSV content
    response = app.response_class(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=history_export_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
    
    return response

@app.route('/api/performance/<path:website>')
def api_performance(website):
    hours = int(request.args.get('hours', 24))
    timestamps, response_times, statuses = monitor.get_performance_data(website, hours)
    
    # Convert timestamps to formatted strings for JSON
    formatted_timestamps = [monitor.format_timestamp(ts) for ts in timestamps]
    
    return jsonify({
        'timestamps': formatted_timestamps,
        'response_times': response_times,
        'statuses': statuses
    })
@app.route('/api/settings/reset-settings-only', methods=['POST'])
@require_auth
def api_reset_settings_only():
    """Reset only settings to default values, keep websites and webhooks"""
    try:
        # Reset settings to default values
        default_settings = {
            'check_interval': 60,
            'timeout': 5,
            'expected_status': 200,
            'performance_threshold': 1000,
            'consecutive_checks': 2,
            'smtp_server': '',
            'smtp_port': 587,
            'smtp_security': 'TLS',
            'smtp_user': '',
            'smtp_pass': '',
            'recipient_email': '',
            'from_name': 'Ping Daddy',
            'subject_prefix': 'Ping Daddy:',
            'notification_method': 'both',
            'timezone': 'UTC',
            'time_format': '%Y-%m-%d %H:%M:%S',
            'theme': 'light'
        }
        
        if monitor.save_settings(default_settings):
            return jsonify({'success': True, 'message': 'Settings reset to default values (websites and webhooks preserved)'})
        else:
            return jsonify({'success': False, 'message': 'Error resetting settings'})
    except Exception as e:
        print(f"Error resetting settings only: {str(e)}")
        return jsonify({'success': False, 'message': f'Error resetting settings: {str(e)}'})

@app.route('/api/settings/reset', methods=['POST'])
@require_auth
def api_reset_settings():
    """Reset all settings to default values"""
    try:
        # Reset settings to default values
        default_settings = {
            'check_interval': 60,
            'timeout': 5,
            'expected_status': 200,
            'performance_threshold': 1000,
            'consecutive_checks': 2,
            'smtp_server': '',
            'smtp_port': 587,
            'smtp_security': 'TLS',
            'smtp_user': '',
            'smtp_pass': '',
            'recipient_email': '',
            'from_name': 'Ping Daddy',
            'subject_prefix': 'Ping Daddy:',
            'notification_method': 'both',
            'timezone': 'UTC',
            'time_format': '%Y-%m-%d %H:%M:%S',
            'theme': 'light',
            'ssl_check_interval': 3600
        }
        
        if monitor.save_settings(default_settings):
            # Stop monitoring to clear memory
            monitor.stop_monitoring()
            
            # Clear websites
            monitor.websites = []
            monitor.save_websites([])
            
            # Clear website status tracking
            monitor.website_status = {}
            monitor.website_expected_texts = {}
            
            # Clear webhooks
            monitor.webhooks = []
            monitor.clear_all_webhooks()
            
            # Clear all other data tables
            cursor, conn = get_db_cursor()
            
            # Clear history data
            cursor.execute('DELETE FROM history')
            
            # Clear performance data
            cursor.execute('DELETE FROM performance_data')
            
            # Clear SSL certificates data
            cursor.execute('DELETE FROM ssl_certificates')
            
            conn.commit()
            conn.close()
            
            # Restart monitoring with clean state
            monitor.start_monitoring()
            
            return jsonify({'success': True, 'message': 'All settings reset to default values'})
        else:
            return jsonify({'success': False, 'message': 'Error resetting settings'})
    except Exception as e:
        print(f"Error resetting settings: {str(e)}")
        return jsonify({'success': False, 'message': f'Error resetting settings: {str(e)}'})

@app.route('/api/settings/test-smtp', methods=['POST'])
def api_test_smtp():
    data = request.json
    success, message = monitor.test_smtp_settings(data)
    return jsonify({'success': success, 'message': message})

@app.route('/api/cleanup', methods=['POST'])
@require_auth
def api_cleanup():
    """Manually trigger cleanup of old data"""
    try:
        monitor.cleanup_old_data()
        return jsonify({'success': True, 'message': 'Cleanup completed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Cleanup failed: {str(e)}'})

@app.route('/api/reset-brute-force', methods=['POST'])
@require_auth
def api_reset_brute_force():
    """Reset brute force lockout for all users (admin only)"""
    try:
        cursor, conn = get_db_cursor()
        
        # Reset all failed attempts and lockouts
        cursor.execute('UPDATE admin_users SET failed_attempts = 0, locked_until = NULL')
        
        # Clear recent login attempts (last 24 hours)
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        cursor.execute('DELETE FROM login_attempts WHERE attempt_time > %s', (twenty_four_hours_ago,))
        
        conn.commit()
        conn.close()
        
        print(f"SECURITY LOG: Brute force lockout reset by admin user: {session.get('username', 'unknown')}")
        return jsonify({'success': True, 'message': 'Brute force lockout reset successfully'})
        
    except Exception as e:
        print(f"Error resetting brute force lockout: {str(e)}")
        return jsonify({'success': False, 'message': f'Reset failed: {str(e)}'})
    
@app.route('/api/performance-chart/<path:website>')
def api_performance_chart(website):
    hours = int(request.args.get('hours', 24))
    timestamps, response_times, statuses = monitor.get_performance_data(website, hours)
    
    if not timestamps:
        return "No data available", 404
    
    # Create performance chart
    plt.figure(figsize=(10, 6))
    
    # Convert statuses to colors
    colors = []
    for status in statuses:
        if status == "Online":
            colors.append('green')
        elif status == "Performance Issue":
            colors.append('orange')
        else:
            colors.append('red')
    
    # Plot response times
    plt.plot(timestamps, response_times, 'b-', alpha=0.7, label='Response Time (ms)')
    plt.scatter(timestamps, response_times, c=colors, s=50, alpha=0.8)
    
    # Add performance threshold line
    plt.axhline(y=monitor.performance_threshold, color='r', linestyle='--', 
                label=f'Threshold ({monitor.performance_threshold}ms)')
    
    plt.title(f'Performance Data for {website}')
    plt.xlabel('Time')
    plt.ylabel('Response Time (ms)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//6)))
    plt.gcf().autofmt_xdate()
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return send_file(buf, mimetype='image/png')

@app.route('/api/ssl-info/<path:website>')
def api_ssl_info(website):
    ssl_info = monitor.get_ssl_info(website)
    if ssl_info:
        def safe_isoformat(dt):
            """Safely convert datetime to ISO format"""
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            try:
                return dt.isoformat()
            except:
                return str(dt)
        
        return jsonify({
            'website': ssl_info['website'],
            'valid_from': safe_isoformat(ssl_info['valid_from']),
            'valid_to': safe_isoformat(ssl_info['valid_to']),
            'issuer': ssl_info['issuer'],
            'last_checked': safe_isoformat(ssl_info['last_checked']),
            'days_remaining': ssl_info['days_remaining']
        })
    else:
        return jsonify({'error': 'No SSL data available'}), 404

@app.route('/api/debug/test-db', methods=['GET', 'POST'])
def api_debug_test_db():
    """Debug endpoint to test direct database insert"""
    try:
        cursor, conn = get_db_cursor()
        
        # Test direct insert
        cursor.execute('''INSERT INTO webhooks (name, url, secret, events, active)
                     VALUES (%s, %s, %s, %s, %s)''', 
                     ('test_webhook', 'https://test.com', '', 'online,offline', 1))
        
        conn.commit()
        print("DEBUG: Direct insert committed")
        
        # Check if it was saved
        cursor.execute('SELECT COUNT(*) FROM webhooks')
        count_result = cursor.fetchone()
        count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
        print(f"DEBUG: Webhooks in database after direct insert: {count}")
        
        # Get all webhooks
        cursor.execute('SELECT * FROM webhooks')
        webhooks = cursor.fetchall()
        print(f"DEBUG: All webhooks in database: {webhooks}")
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': count,
            'webhooks': webhooks
        })
    except Exception as e:
        print(f"DEBUG: Error in test-db: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug/history')
def api_debug_history():
    """Debug endpoint to check history in database"""
    try:
        cursor, conn = get_db_cursor()
        
        # Get all history from database
        cursor.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT 10')
        history = cursor.fetchall()
        
        # Get count
        cursor.execute('SELECT COUNT(*) FROM history')
        count_result = cursor.fetchone()
        count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'database_count': count,
            'database_history': history,
            'websites_count': len(monitor.websites),
            'websites': monitor.websites
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug/webhooks')
def api_debug_webhooks():
    """Debug endpoint to check webhooks in database"""
    try:
        cursor, conn = get_db_cursor()
        
        # Get all webhooks from database
        cursor.execute('SELECT * FROM webhooks')
        webhooks = cursor.fetchall()
        
        # Get count
        cursor.execute('SELECT COUNT(*) FROM webhooks')
        count_result = cursor.fetchone()
        count = count_result['count'] if isinstance(count_result, dict) else count_result[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'database_count': count,
            'database_webhooks': webhooks,
            'memory_count': len(monitor.webhooks),
            'memory_webhooks': monitor.webhooks
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug/brute-force')
def api_debug_brute_force():
    """Debug endpoint to check brute force protection status"""
    try:
        cursor, conn = get_db_cursor()
        
        # Get admin users
        cursor.execute('SELECT username, failed_attempts, locked_until, last_login FROM admin_users')
        admin_users = cursor.fetchall()
        
        # Get recent login attempts
        cursor.execute('''SELECT ip_address, username, attempt_time, success 
                         FROM login_attempts 
                         ORDER BY attempt_time DESC LIMIT 20''')
        login_attempts = cursor.fetchall()
        
        # Get IP attempt counts in last 15 minutes
        fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
        cursor.execute('''SELECT ip_address, COUNT(*) as attempts 
                         FROM login_attempts 
                         WHERE attempt_time > %s AND success = FALSE 
                         GROUP BY ip_address 
                         ORDER BY attempts DESC''', (fifteen_minutes_ago,))
        ip_attempts = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'admin_users': admin_users,
            'recent_login_attempts': login_attempts,
            'ip_attempts_last_15min': ip_attempts,
            'current_time': datetime.now().isoformat(),
            'fifteen_minutes_ago': fifteen_minutes_ago.isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/is-monitoring')
def api_is_monitoring():
    return jsonify({'is_monitoring': monitor.is_monitoring})

if __name__ == '__main__':
    # Initialize database and create admin user if needed
    init_db()
    
    # Start monitoring automatically
    monitor.start_monitoring()
    
    # Enable debug mode based on environment variables
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true' or os.environ.get('FLASK_ENV', 'production').lower() == 'development'
    
    # Run with SocketIO
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

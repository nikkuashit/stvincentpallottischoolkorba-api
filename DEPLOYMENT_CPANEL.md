# cPanel Deployment Guide

## Prerequisites

- cPanel hosting account with Python support (3.9+)
- SSH access to your server
- Domain or subdomain configured in cPanel
- MySQL or PostgreSQL database (recommended for production)

## Step 1: Setup Python Environment in cPanel

1. **Login to cPanel**

2. **Create Python Application**
   - Go to: Software → Setup Python App
   - Click "Create Application"
   - Configure:
     - Python Version: 3.11 or higher
     - Application Root: `/home/username/stvincentpallottischoolkorba-api`
     - Application URL: `api.yourdomain.com` or `/api`
     - Application Startup File: `passenger_wsgi.py`
     - Application Entry Point: `application`

3. **Note the Virtual Environment Path**
   - cPanel will create a virtual environment
   - Example: `/home/username/virtualenv/stvincentpallottischoolkorba-api/3.11`

## Step 2: Upload Your Code

### Option A: Via Git (Recommended)

```bash
# SSH into your server
ssh username@yourdomain.com

# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/nikkuashit/stvincentpallottischoolkorba-api.git

# Navigate to project
cd stvincentpallottischoolkorba-api
```

### Option B: Via FTP/File Manager
- Use cPanel File Manager or FTP client
- Upload all files to `/home/username/stvincentpallottischoolkorba-api`
- Ensure all Python files are uploaded

## Step 3: Install Dependencies

```bash
# Activate virtual environment (path from cPanel Python App)
source /home/username/virtualenv/stvincentpallottischoolkorba-api/3.11/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Create Database

1. **Via cPanel → MySQL Databases**
   - Database name: `username_schooldb`
   - Database user: `username_schooluser`
   - Grant ALL PRIVILEGES

2. **Note credentials:**
   - Host: `localhost`
   - Database: `username_schooldb`
   - Username: `username_schooluser`
   - Password: [your password]

## Step 5: Configure Environment Variables

Create `.env` file in project root:

```bash
# SSH into your server
cd ~/stvincentpallottischoolkorba-api

# Create .env file
nano .env
```

Add configuration:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com,www.yourdomain.com

# Database Configuration (MySQL)
DB_ENGINE=django.db.backends.mysql
DB_NAME=username_schooldb
DB_USER=username_schooluser
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=3306

# For PostgreSQL (if available)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=username_schooldb
# DB_USER=username_schooluser
# DB_PASSWORD=your-database-password
# DB_HOST=localhost
# DB_PORT=5432

# CORS Settings
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# JWT Settings
JWT_SECRET_KEY=another-secret-key-for-jwt-tokens
```

Save and exit (Ctrl+X, then Y, then Enter)

## Step 6: Update Django Settings

Update `school_api/settings.py` for production:

```python
# Add at the top
from decouple import config

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Whitenoise for serving static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## Step 7: Run Migrations and Collect Static Files

```bash
# Activate virtual environment
source /home/username/virtualenv/stvincentpallottischoolkorba-api/3.11/bin/activate

# Navigate to project
cd ~/stvincentpallottischoolkorba-api

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Step 8: Update .htaccess

Edit `.htaccess` file with your actual paths:

```apache
PassengerEnabled On
PassengerAppRoot /home/username/stvincentpallottischoolkorba-api
PassengerPython /home/username/virtualenv/stvincentpallottischoolkorba-api/3.11/bin/python3.11
```

## Step 9: Set Directory Permissions

```bash
# Set correct permissions
chmod 755 ~/stvincentpallottischoolkorba-api
chmod 644 ~/stvincentpallottischoolkorba-api/.htaccess
chmod 644 ~/stvincentpallottischoolkorba-api/passenger_wsgi.py
chmod 600 ~/stvincentpallottischoolkorba-api/.env

# Make media directory writable
chmod 755 ~/stvincentpallottischoolkorba-api/media
chmod 755 ~/stvincentpallottischoolkorba-api/staticfiles
```

## Step 10: Restart Application

In cPanel:
1. Go to: Software → Setup Python App
2. Find your application
3. Click "Restart" button

Or via SSH:
```bash
touch ~/stvincentpallottischoolkorba-api/tmp/restart.txt
```

## Step 11: Test Your Deployment

Visit your URLs:
- Main site: `https://yourdomain.com/api/`
- Admin panel: `https://yourdomain.com/api/admin/`
- API docs: `https://yourdomain.com/api/swagger/`

## Troubleshooting

### Check Error Logs
```bash
# Passenger log
cat ~/passenger.log

# Application log (if configured)
cat ~/stvincentpallottischoolkorba-api/logs/django.log
```

### Common Issues

1. **500 Internal Server Error**
   - Check `.env` file exists and has correct values
   - Verify database credentials
   - Check Python version matches
   - Review error logs

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic` again
   - Check STATIC_ROOT path in settings
   - Verify .htaccess rules for static files

3. **Database Connection Error**
   - Verify database exists in cPanel
   - Check database user has privileges
   - Confirm credentials in .env file

4. **Module Not Found Error**
   - Activate virtual environment
   - Reinstall requirements: `pip install -r requirements.txt`

5. **Permission Denied**
   - Check file permissions (755 for directories, 644 for files)
   - Ensure .env is 600 (not readable by others)

## Updating Your Application

```bash
# SSH into server
cd ~/stvincentpallottischoolkorba-api

# Pull latest changes
git pull origin main

# Activate virtual environment
source /home/username/virtualenv/stvincentpallottischoolkorba-api/3.11/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application
touch tmp/restart.txt
```

## Security Checklist

- ✅ DEBUG=False in production
- ✅ Strong SECRET_KEY (use Django's get_random_secret_key())
- ✅ .env file permissions set to 600
- ✅ ALLOWED_HOSTS configured
- ✅ Database credentials secured
- ✅ CORS properly configured
- ✅ SSL/HTTPS enabled
- ✅ Regular backups configured

## Performance Optimization

1. **Enable Database Connection Pooling**
2. **Configure Redis for caching** (if available)
3. **Enable Gzip compression** in .htaccess
4. **Use CDN for static files**
5. **Optimize database queries**

## Monitoring

- Setup error email notifications in Django settings
- Use cPanel's Resource Usage tool
- Monitor application logs regularly
- Setup uptime monitoring (e.g., UptimeRobot)

## Support

For issues specific to:
- Django: https://docs.djangoproject.com/
- cPanel: Contact your hosting provider
- Application: https://github.com/nikkuashit/stvincentpallottischoolkorba-api/issues

---

**Need Help?** Create an issue on GitHub or contact your hosting provider for cPanel-specific support.

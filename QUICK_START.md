# Quick Start Guide

## ✅ Setup Complete!

Your Vulnerability Management System is now ready to use. Here's what was successfully set up:

### 🎯 What's Working
- ✅ Django application with SQLite database
- ✅ AdminLTE dashboard interface
- ✅ All three repository apps (CPE, CVE, Linux CVE Announcements)
- ✅ REST APIs with full functionality
- ✅ Management commands for data import
- ✅ Production-ready Waitress server
- ✅ Database migrations applied
- ✅ Static files collected
- ✅ Sample CVE data imported (46 records)

### 🚀 Start the Application

#### Development Server
```bash
source venv/bin/activate
python manage.py runserver
```
Access at: http://127.0.0.1:8000

#### Production Server
```bash
source venv/bin/activate
python run_server.py
```
Access at: http://127.0.0.1:8000

### 📊 Dashboard Features

1. **Main Dashboard** (`/`)
   - Overview statistics
   - Recent import activity
   - Quick navigation

2. **CPE Repository** (`/cpe/`)
   - Browse Common Platform Enumeration entries
   - Search and filter functionality

3. **CVE Repository** (`/cve/`)
   - Browse Common Vulnerabilities and Exposures
   - Filter by severity, year
   - Detailed CVSS information

4. **Linux CVE Announcements** (`/linux-cve/`)
   - Browse Linux kernel CVE announcements
   - Search by content and sender

5. **Admin Interface** (`/admin/`)
   - Username: (your created superuser)
   - Full Django admin functionality

### 🔌 API Endpoints

All APIs support pagination, search, and filtering:

```bash
# CVE API
curl http://127.0.0.1:8000/api/cve/
curl http://127.0.0.1:8000/api/cve/?search=apache
curl http://127.0.0.1:8000/api/cve/CVE-1999-0001/

# CPE API  
curl http://127.0.0.1:8000/api/cpe/
curl http://127.0.0.1:8000/api/cpe/?vendor=apache

# Linux CVE API
curl http://127.0.0.1:8000/api/linux-cve/
```

### 📥 Import Data

#### Import CVE Data (Recommended first)
```bash
source venv/bin/activate

# Import recent CVEs (safe date range for systems with date issues)
python manage.py import_cve --safe-date

# Import recent CVEs (last 7 days - may fail if system date is wrong)
python manage.py import_cve

# Import specific time range
python manage.py import_cve --days-back 30 --safe-date

# Full import (takes hours, 300k+ records)
python manage.py import_cve --full
```

#### Import CPE Data
```bash
# Import recent CPE updates
python manage.py import_cpe

# Full CPE import (takes time, 900k+ records)
python manage.py import_cpe --full
```

#### Import Linux CVE Announcements
```bash
# Test local server connectivity first
python test_linux_cve_server.py

# Import from local server (default: http://localhost:8080/linux-cve-announce)
python manage.py import_linux_cve --limit 10

# Import from custom URL
python manage.py import_linux_cve --base-url http://your-server:port/path --limit 50

# Full import from local server
python manage.py import_linux_cve --full
```

### ⚡ Performance Tips

1. **Get NVD API Key** (Highly Recommended)
   - Register at: https://nvd.nist.gov/developers/request-an-api-key
   - Add to `.env`: `NVD_API_KEY=your-key-here`
   - Increases rate limit from 5 to 50 requests per 30 seconds

2. **Batch Size Optimization**
   ```bash
   # With API key, use larger batches
   python manage.py import_cve --batch-size 2000
   
   # Without API key, use smaller batches
   python manage.py import_cve --batch-size 100
   ```

3. **Scheduled Updates**
   ```bash
   # Set up daily updates (see scripts/cron_example.txt)
   0 2 * * * /path/to/project/venv/bin/python /path/to/project/scripts/update_data.py
   ```

### 🔧 Configuration

Edit `.env` file for customization:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
NVD_API_KEY=your-nvd-api-key
HOST=0.0.0.0
PORT=8000
```

### 📁 Key Directories

- `logs/` - Application and import logs
- `db.sqlite3` - SQLite database file
- `staticfiles/` - Collected static files (generated)
- `static/` - Source static files (AdminLTE assets)
- `venv/` - Python virtual environment

### 🆘 Troubleshooting

1. **Import Rate Limiting**
   - Get NVD API key
   - Increase `--delay` parameter
   - Use smaller `--batch-size`

2. **Date-related Import Errors (404 errors)**
   ```bash
   # If you get 404 errors with date filtering, use safe-date option
   python manage.py import_cve --safe-date
   python manage.py import_cpe --full  # CPE doesn't have safe-date, use full
   ```

3. **Duplicate Constraint Errors**
   ```bash
   # If you get UNIQUE constraint errors, clean up duplicates first
   python manage.py cleanup_cve_duplicates
   python manage.py import_cve --batch-size 50
   ```

3. **Static Files Issues**
   ```bash
   python manage.py collectstatic --clear
   ```

4. **Database Issues**
   ```bash
   python manage.py migrate
   ```

5. **Check Logs**
   ```bash
   tail -f logs/vulnmgmt.log
   ```

### 🎯 Next Steps

1. **Import More Data**: Start with CVE data for recent vulnerabilities
2. **Set Up Monitoring**: Configure log monitoring and alerts
3. **Schedule Updates**: Set up cron jobs for automatic data updates
4. **Customize**: Add new data sources or modify existing ones
5. **Scale**: Consider PostgreSQL for larger deployments

### 📚 Documentation

- Full documentation: `README.md`
- Project structure: `PROJECT_STRUCTURE.md`
- API examples in README.md
- Deployment guides for Linux/Windows

---

**🎉 Congratulations!** Your vulnerability management system is ready for production use.
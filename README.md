# Vulnerability Management System

A Django-based web application for local vulnerability management, acting as a local repository of security information from various sources across the Internet.

## Features

- **CPE Repository**: Local mirror of NVD Common Platform Enumeration dictionary
- **CVE Repository**: Local repository of Common Vulnerabilities and Exposures from NVD
- **Linux CVE Announcements**: Local mirror of Linux kernel CVE announcements
- **Web Interface**: AdminLTE-based dashboard for browsing and searching
- **REST APIs**: Full REST API access to all data
- **Automated Updates**: Scheduled import and update mechanisms
- **Cross-Platform**: Runs on Linux and Windows

## Architecture

- **Framework**: Django 4.2 LTS
- **Database**: SQLite (production-ready for this use case)
- **Application Server**: Waitress
- **Frontend**: AdminLTE 3.2.0 dashboard template
- **APIs**: Django REST Framework

## Quick Start

### Linux

```bash
# Clone the repository
git clone <repository-url>
cd vulnerability-management

# Run setup script
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh

# Start the server
source venv/bin/activate
python run_server.py
```

### Windows

```cmd
REM Clone the repository
git clone <repository-url>
cd vulnerability-management

REM Run setup script
scripts\setup_windows.bat

REM Start the server
venv\Scripts\activate.bat
python run_server.py
```

## Detailed Installation

### Prerequisites

- Python 3.8 or higher
- Internet connection for data imports
- At least 2GB free disk space (for full data imports)

### Step 1: Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate.bat`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Configuration

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
   NVD_API_KEY=your-nvd-api-key  # Optional but recommended
   ```

**Note**: AdminLTE assets are included in the `static/` directory. No external dependencies required.

### Step 3: Database Setup

1. Run migrations:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

### Step 4: Data Import

Import data from various sources:

```bash
# Import CPE data (this may take a while)
python manage.py import_cpe

# Import CVE data (this may take a while)
python manage.py import_cve

# Import Linux CVE announcements
python manage.py import_linux_cve
```

### Step 5: Start the Server

For production:
```bash
python run_server.py
```

For development:
```bash
python manage.py runserver
```

## Data Sources

### CPE Repository
- **Source**: NVD CPE Dictionary API
- **URL**: https://services.nvd.nist.gov/rest/json/cpes/2.0/
- **Documentation**: https://nvd.nist.gov/products/cpe
- **Update Frequency**: Weekly (recommended)

### CVE Repository
- **Source**: NVD CVE API
- **URL**: https://services.nvd.nist.gov/rest/json/cves/2.0/
- **Documentation**: https://nvd.nist.gov/developers/vulnerabilities
- **Update Frequency**: Daily (recommended)

### Linux CVE Announcements
- **Source**: Linux CVE Announce Mailing List
- **URL**: https://lore.kernel.org/linux-cve-announce/
- **Documentation**: https://lore.kernel.org/linux-cve-announce/_/text/mirror/
- **Update Frequency**: Daily (recommended)

## API Usage

All repositories expose REST APIs:

### CPE API
```bash
# List CPEs
GET /api/cpe/

# Search CPEs
GET /api/cpe/?search=apache

# Filter by vendor
GET /api/cpe/?vendor=apache

# Get CPE details
GET /api/cpe/{cpe_name_id}/

# Get statistics
GET /api/cpe/stats/
```

### CVE API
```bash
# List CVEs
GET /api/cve/

# Search CVEs
GET /api/cve/?search=apache

# Filter by severity
GET /api/cve/?severity=HIGH

# Filter by year
GET /api/cve/?year=2023

# Get CVE details
GET /api/cve/{cve_id}/

# Get statistics
GET /api/cve/stats/
```

### Linux CVE Announcements API
```bash
# List announcements
GET /api/linux-cve/

# Search announcements
GET /api/linux-cve/?search=kernel

# Filter by sender
GET /api/linux-cve/?sender=example@kernel.org

# Get announcement details
GET /api/linux-cve/{message_id}/

# Get statistics
GET /api/linux-cve/stats/
```

## Scheduled Updates

### Linux (Cron)

Add to your crontab (`crontab -e`):

```bash
# Daily update at 2 AM
0 2 * * * /path/to/project/venv/bin/python /path/to/project/scripts/update_data.py

# CVE updates every 6 hours
0 */6 * * * /path/to/project/venv/bin/python /path/to/project/manage.py import_cve

# Weekly full CPE update on Sunday at 3 AM
0 3 * * 0 /path/to/project/venv/bin/python /path/to/project/manage.py import_cpe --full
```

### Windows (Task Scheduler)

1. Import the provided XML file:
   ```cmd
   schtasks /create /xml scripts\windows_task_scheduler.xml /tn "VulnMgmt Daily Update"
   ```

2. Or create manually:
   - Open Task Scheduler
   - Create Basic Task
   - Set trigger (daily at 2 AM)
   - Set action to run: `python scripts\update_data.py`

## Management Commands

### CPE Import
```bash
# Full import
python manage.py import_cpe --full

# Incremental import (default)
python manage.py import_cpe

# Custom batch size and delay
python manage.py import_cpe --batch-size 1000 --delay 3
```

### CVE Import
```bash
# Full import
python manage.py import_cve --full

# Incremental import (default, last 7 days)
python manage.py import_cve

# Custom time range
python manage.py import_cve --days-back 30
```

### Linux CVE Import
```bash
# Import announcements
python manage.py import_linux_cve

# Limit for testing
python manage.py import_linux_cve --limit 50
```

## Extending the Application

### Adding New Data Sources

1. Create a new Django app:
   ```bash
   python manage.py startapp new_repository
   ```

2. Add to `INSTALLED_APPS` in `settings.py`

3. Create models inheriting from `BaseModel`:
   ```python
   from apps.core.models import BaseModel
   
   class NewDataModel(BaseModel):
       # Your fields here
       pass
   ```

4. Create management commands for data import

5. Add API views and serializers

6. Create web templates

7. Update URLs and navigation

### Shared Components

The `apps.core` app provides shared functionality:

- `BaseModel`: Common fields (created_at, updated_at)
- `ImportLog`: Track import operations
- Dashboard views
- Global search functionality

## Configuration

### Environment Variables

- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Debug mode (default: True)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `NVD_API_KEY`: NVD API key for higher rate limits
- `NVD_REQUEST_DELAY`: Delay between API requests in seconds
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 8000)

### NVD API Key

While optional, an NVD API key is highly recommended:

1. Register at: https://nvd.nist.gov/developers/request-an-api-key
2. Add to your `.env` file: `NVD_API_KEY=your-key-here`
3. Benefits: Higher rate limits (50 requests/30 seconds vs 5 requests/30 seconds)

## Troubleshooting

### Common Issues

1. **Import fails with rate limiting**:
   - Get an NVD API key
   - Increase `NVD_REQUEST_DELAY`

2. **Database locked errors**:
   - Ensure only one import runs at a time
   - Check disk space

3. **Static files not loading**:
   - Run `python manage.py collectstatic`
   - Check `STATIC_ROOT` setting

4. **AdminLTE assets missing**:
   - Ensure `AdminLTE-3.2.0` folder exists
   - Check `STATICFILES_DIRS` setting

### Logs

Check logs in the `logs/` directory:
- `vulnmgmt.log`: Application logs
- `update_data.log`: Data update logs

## Security Considerations

- Change the default `SECRET_KEY`
- Set `DEBUG=False` in production
- Use HTTPS in production
- Regularly update dependencies
- Monitor disk space for database growth
- Consider database backups

## Performance

### Database Optimization

The application uses SQLite with proper indexing:
- Indexes on frequently queried fields
- Pagination for large datasets
- Efficient queries with select_related/prefetch_related

### Scaling Considerations

For large deployments:
- Consider PostgreSQL for better concurrent access
- Use Redis for caching
- Implement database connection pooling
- Use a reverse proxy (nginx/Apache)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Create an issue on GitHub

## Acknowledgments

- NVD for providing the CVE and CPE data
- Linux kernel team for the CVE announcements
- AdminLTE for the dashboard template
- Django and Django REST Framework communities
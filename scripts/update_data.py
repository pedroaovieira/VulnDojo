#!/usr/bin/env python
"""
Data update script for scheduled tasks
"""
import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vulnmgmt.settings')

# Setup Django
django.setup()

from django.core.management import call_command
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_dir, 'logs', 'update_data.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def update_cpe_data():
    """Update CPE data."""
    logger.info("Starting CPE data update...")
    try:
        call_command('import_cpe')
        logger.info("CPE data update completed successfully")
    except Exception as e:
        logger.error(f"CPE data update failed: {e}")

def update_cve_data():
    """Update CVE data."""
    logger.info("Starting CVE data update...")
    try:
        call_command('import_cve')
        logger.info("CVE data update completed successfully")
    except Exception as e:
        logger.error(f"CVE data update failed: {e}")

def update_linux_cve_data():
    """Update Linux CVE announcements."""
    logger.info("Starting Linux CVE announcements update...")
    try:
        call_command('import_linux_cve')
        logger.info("Linux CVE announcements update completed successfully")
    except Exception as e:
        logger.error(f"Linux CVE announcements update failed: {e}")

def main():
    """Main update function."""
    logger.info("=" * 50)
    logger.info(f"Starting data update at {datetime.now()}")
    logger.info("=" * 50)
    
    # Update all data sources
    update_cpe_data()
    update_cve_data()
    update_linux_cve_data()
    
    logger.info("=" * 50)
    logger.info(f"Data update completed at {datetime.now()}")
    logger.info("=" * 50)

if __name__ == '__main__':
    main()
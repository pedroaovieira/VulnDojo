import requests
import email
import re
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.core.models import ImportLog
from apps.linux_cve_announcements.models import LinuxCVEAnnouncement, LinuxCVEAnnouncementCVE

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import Linux CVE announcements from lore.kernel.org'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Perform full import (default is incremental)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of messages to process (for testing)',
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8080/linux-cve-announce',
            help='Base URL for the Linux CVE announcements server',
        )
    
    def handle(self, *args, **options):
        import_log = ImportLog.objects.create(
            import_type='linux_cve',
            status='started'
        )
        
        try:
            self.import_linux_cve_data(
                import_log=import_log,
                full_import=options['full'],
                limit=options['limit'],
                base_url=options['base_url']
            )
            import_log.mark_completed()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported Linux CVE announcements. '
                    f'Processed: {import_log.records_processed}, '
                    f'Created: {import_log.records_created}, '
                    f'Updated: {import_log.records_updated}'
                )
            )
        except Exception as e:
            error_msg = str(e)
            import_log.mark_failed(error_msg)
            self.stdout.write(self.style.ERROR(f'Import failed: {error_msg}'))
            raise
    
    def import_linux_cve_data(self, import_log, full_import=False, limit=100, base_url='http://localhost:8080/linux-cve-announce'):
        """Import Linux CVE announcements from local server."""
        
        # Get the list of messages
        try:
            response = requests.get(f'{base_url}/', timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch message list from {base_url}: {e}")
        
        # Parse message links from the HTML
        message_links = self.extract_message_links(response.text, base_url)
        
        if limit:
            message_links = message_links[:limit]
        
        self.stdout.write(f'Found {len(message_links)} messages to process from {base_url}')
        
        for i, message_link in enumerate(message_links):
            if i % 10 == 0:
                self.stdout.write(f'Processing message {i+1}/{len(message_links)}')
            
            try:
                self.process_message(message_link, import_log)
            except Exception as e:
                logger.error(f"Failed to process message {message_link}: {e}")
                continue
    
    def extract_message_links(self, html_content, base_url):
        """Extract message links from the HTML."""
        # Pattern for the specific format used by the local server
        # Links can be in different formats:
        # - href="message-id/T/#t" or href="message-id/T/#u" 
        # - href="?t=timestamp"
        patterns = [
            r'href="([^"]*[0-9a-f-]+/T/#[tu])"',  # Thread format: message-id/T/#t
            r'href="([^"]*[0-9a-f-]+)"',  # Direct message ID format
            r'href="(\?t=[0-9]+)"',  # Query parameter format: ?t=timestamp
        ]
        
        links = []
        for pattern in patterns:
            found_links = re.findall(pattern, html_content)
            links.extend(found_links)
        
        # Convert relative links to absolute and clean them up
        full_links = []
        for link in links:
            # Clean up thread suffixes
            clean_link = link.replace('/T/#t', '').replace('/T/#u', '')
            
            if clean_link.startswith('?'):
                # Query parameter format
                full_links.append(f'{base_url}/{clean_link}')
            elif clean_link.startswith('/'):
                # Absolute path, use the same host
                host = base_url.split('/')[2]  # Extract host from base_url
                protocol = base_url.split('://')[0]
                full_links.append(f'{protocol}://{host}{clean_link}')
            elif not clean_link.startswith('http'):
                # Relative path
                full_links.append(f'{base_url}/{clean_link}')
            else:
                # Already absolute
                full_links.append(clean_link)
        
        # Remove duplicates and filter out non-message links
        unique_links = list(set(full_links))
        
        # Filter to only include likely message links
        message_links = []
        for link in unique_links:
            # Skip common non-message links
            if any(skip in link.lower() for skip in ['css', 'js', 'img', 'favicon', 'robots.txt', 'help', 'color', 'mirror', 'atom']):
                continue
            # Include links that look like message IDs or timestamps
            if re.search(r'[0-9a-f-]{10,}', link) or '?t=' in link:
                message_links.append(link)
        
        return message_links
    
    def process_message(self, message_url, import_log):
        """Process a single message from the mailing list."""
        # For the local server format, try different approaches to get raw content
        raw_content = None
        
        # Try different raw content paths based on the local server structure
        raw_urls = [
            f"{message_url}/raw",
            f"{message_url}.txt",
            f"{message_url}/t.mbox.gz",
            f"{message_url}/t.atom",
            message_url,  # Sometimes the message URL itself contains the content
        ]
        
        for raw_url in raw_urls:
            try:
                response = requests.get(raw_url, timeout=30)
                if response.status_code == 200:
                    raw_content = response.text
                    # Check if this looks like email content
                    if 'Message-ID:' in raw_content or 'From:' in raw_content or 'Subject:' in raw_content:
                        break
            except requests.RequestException:
                continue
        
        if raw_content is None:
            logger.error(f"Failed to fetch raw message content from {message_url}")
            return
        
        # Parse email
        try:
            msg = email.message_from_string(raw_content)
        except Exception as e:
            logger.error(f"Failed to parse email from {message_url}: {e}")
            return
        
        # Extract message ID
        message_id = msg.get('Message-ID', '').strip('<>')
        if not message_id:
            # Generate a message ID from the URL if not present
            if '?t=' in message_url:
                # Extract timestamp from query parameter
                message_id = message_url.split('?t=')[1]
            else:
                message_id = message_url.split('/')[-1]
                if not message_id:
                    message_id = message_url.split('/')[-2]  # Try parent directory
            
            # Ensure message_id is not empty and is unique
            if not message_id:
                message_id = f"url_{hash(message_url)}"
            
            logger.warning(f"No Message-ID found, using URL-based ID: {message_id}")
        
        # Check if we already have this message
        if LinuxCVEAnnouncement.objects.filter(message_id=message_id).exists():
            return  # Skip existing messages
        
        # Extract other fields
        subject = msg.get('Subject', '')
        sender = msg.get('From', '')
        date_str = msg.get('Date', '')
        
        # Parse date
        try:
            date = parsedate_to_datetime(date_str)
            if date.tzinfo is None:
                date = timezone.make_aware(date)
        except Exception:
            date = timezone.now()
        
        # Extract content
        content = self.extract_email_content(msg)
        
        # If content is empty, try to extract from raw content
        if not content.strip():
            content = raw_content
        
        # Create announcement
        with transaction.atomic():
            announcement = LinuxCVEAnnouncement.objects.create(
                message_id=message_id,
                subject=subject,
                sender=sender,
                date=date,
                content=content,
                raw_content=raw_content,
            )
            
            # Extract and store CVE IDs
            cve_ids = announcement.cve_ids
            for cve_id in cve_ids:
                # Use get_or_create to avoid duplicates
                LinuxCVEAnnouncementCVE.objects.get_or_create(
                    announcement=announcement,
                    cve_id=cve_id
                )
            
            import_log.records_processed += 1
            import_log.records_created += 1
            import_log.save()
            
            self.stdout.write(f"Imported: {subject[:50]}... (CVEs: {len(cve_ids)})")
    
    def extract_email_content(self, msg):
        """Extract text content from email message."""
        content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception:
                        content += str(part.get_payload())
        else:
            try:
                content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception:
                content = str(msg.get_payload())
        
        return content
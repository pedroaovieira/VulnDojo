import requests
import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from apps.core.models import ImportLog
from apps.cpe_repository.models import CPE, CPEReference

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import CPE data from NVD API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Perform full import (default is incremental)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2000,
            help='Number of records per API request (max 2000)',
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=settings.NVD_REQUEST_DELAY,
            help='Delay between API requests in seconds',
        )
    
    def handle(self, *args, **options):
        import_log = ImportLog.objects.create(
            import_type='cpe',
            status='started'
        )
        
        try:
            self.import_cpe_data(
                import_log=import_log,
                full_import=options['full'],
                batch_size=options['batch_size'],
                delay=options['delay']
            )
            import_log.mark_completed()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported CPE data. '
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
    
    def import_cpe_data(self, import_log, full_import=False, batch_size=2000, delay=6):
        """Import CPE data from NVD API."""
        base_url = f"{settings.NVD_API_BASE_URL}/cpes/2.0"
        headers = {}
        
        if settings.NVD_API_KEY:
            headers['apiKey'] = settings.NVD_API_KEY
            delay = 0.6  # Faster rate with API key
        
        # Determine last modified date for incremental import
        last_modified_start = None
        if not full_import:
            last_cpe = CPE.objects.order_by('-last_modified').first()
            if last_cpe:
                # Ensure we don't use future dates
                if last_cpe.last_modified.year > 2024:
                    from datetime import datetime
                    safe_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
                    last_modified_start = safe_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                else:
                    last_modified_start = last_cpe.last_modified.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        start_index = 0
        total_results = None
        
        while True:
            params = {
                'resultsPerPage': batch_size,
                'startIndex': start_index,
            }
            
            if last_modified_start:
                params['lastModStartDate'] = last_modified_start
            
            self.stdout.write(f'Fetching CPE data (start: {start_index})...')
            
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                if "404" in str(e) and 'lastModStartDate' in params:
                    # If 404 with date filter, try without date filter
                    self.stdout.write(f'Date-filtered request failed, trying full import...')
                    params.pop('lastModStartDate', None)
                    try:
                        response = requests.get(base_url, params=params, headers=headers, timeout=30)
                        response.raise_for_status()
                        data = response.json()
                    except requests.RequestException as e2:
                        raise Exception(f"API request failed: {e2}")
                else:
                    raise Exception(f"API request failed: {e}")
            
            if total_results is None:
                total_results = data.get('totalResults', 0)
                self.stdout.write(f'Total results: {total_results}')
            
            products = data.get('products', [])
            if not products:
                break
            
            self.process_cpe_batch(products, import_log)
            
            start_index += len(products)
            
            # Check if we've processed all results
            if start_index >= total_results:
                break
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
    
    def process_cpe_batch(self, products, import_log):
        """Process a batch of CPE products."""
        with transaction.atomic():
            for product_data in products:
                cpe_data = product_data.get('cpe', {})
                
                cpe_name = cpe_data.get('cpeName')
                cpe_name_id = cpe_data.get('cpeNameId')
                
                if not cpe_name or not cpe_name_id:
                    continue
                
                # Parse last modified date
                last_modified_str = cpe_data.get('lastModified')
                if last_modified_str:
                    last_modified = timezone.make_aware(datetime.fromisoformat(
                        last_modified_str.replace('Z', '')
                    ))
                else:
                    last_modified = timezone.now()
                
                # Get or create CPE
                cpe, created = CPE.objects.get_or_create(
                    cpe_name_id=cpe_name_id,
                    defaults={
                        'cpe_name': cpe_name,
                        'last_modified': last_modified,
                    }
                )
                
                # Update CPE data
                updated = False
                if cpe.cpe_name != cpe_name:
                    cpe.cpe_name = cpe_name
                    updated = True
                
                if cpe.last_modified != last_modified:
                    cpe.last_modified = last_modified
                    updated = True
                
                # Update titles
                titles = cpe_data.get('titles', [])
                if titles:
                    title = titles[0].get('title', '')
                    if cpe.title != title:
                        cpe.title = title
                        updated = True
                
                # Update deprecated status
                deprecated = cpe_data.get('deprecated', False)
                if cpe.deprecated != deprecated:
                    cpe.deprecated = deprecated
                    updated = True
                
                # Update deprecated_by
                deprecated_by = cpe_data.get('deprecatedBy', [])
                if cpe.deprecated_by != deprecated_by:
                    cpe.deprecated_by = deprecated_by
                    updated = True
                
                if updated:
                    cpe.save()
                
                # Handle references
                refs = cpe_data.get('refs', [])
                existing_refs = set(cpe.references.values_list('href', flat=True))
                
                for ref_data in refs:
                    href = ref_data.get('ref')
                    if href and href not in existing_refs:
                        CPEReference.objects.create(
                            cpe=cpe,
                            href=href,
                            text=ref_data.get('text', '')
                        )
                
                # Update counters
                import_log.records_processed += 1
                if created:
                    import_log.records_created += 1
                elif updated:
                    import_log.records_updated += 1
            
            import_log.save()
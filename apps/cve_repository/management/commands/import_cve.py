import requests
import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from apps.core.models import ImportLog
from apps.cve_repository.models import (
    CVE, CVSSMetric, CVEReference, CVEWeakness, 
    CVEConfiguration, CVEConfigurationNode
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import CVE data from NVD API'
    
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
        parser.add_argument(
            '--days-back',
            type=int,
            default=7,
            help='For incremental import, how many days back to check',
        )
        parser.add_argument(
            '--safe-date',
            action='store_true',
            help='Use a safe date range (2024) for incremental import',
        )
    
    def handle(self, *args, **options):
        import_log = ImportLog.objects.create(
            import_type='cve',
            status='started'
        )
        
        try:
            self.import_cve_data(
                import_log=import_log,
                full_import=options['full'],
                batch_size=options['batch_size'],
                delay=options['delay'],
                days_back=options['days_back'],
                safe_date=options['safe_date']
            )
            import_log.mark_completed()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported CVE data. '
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
    
    def import_cve_data(self, import_log, full_import=False, batch_size=2000, delay=6, days_back=7, safe_date=False):
        """Import CVE data from NVD API."""
        base_url = f"{settings.NVD_API_BASE_URL}/cves/2.0"
        headers = {}
        
        if settings.NVD_API_KEY:
            headers['apiKey'] = settings.NVD_API_KEY
            delay = 0.6  # Faster rate with API key
        
        # Determine date range for incremental import
        last_mod_start_date = None
        if not full_import:
            from datetime import timedelta, datetime
            if safe_date:
                # Use a safe date range for systems with incorrect dates
                target_date = datetime(2024, 12, 1, tzinfo=timezone.utc)
            else:
                # Use a reasonable date range - don't go beyond current real date
                target_date = timezone.now() - timedelta(days=days_back)
                # If the target date is in the future (due to system date issues), use a safe past date
                if target_date.year > 2024:
                    target_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
            last_mod_start_date = target_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        start_index = 0
        total_results = None
        
        while True:
            params = {
                'resultsPerPage': batch_size,
                'startIndex': start_index,
            }
            
            if last_mod_start_date:
                params['lastModStartDate'] = last_mod_start_date
            
            self.stdout.write(f'Fetching CVE data (start: {start_index})...')
            
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                if "404" in str(e) and last_mod_start_date:
                    # If 404 with date filter, try without date filter (full import)
                    self.stdout.write(f'Date-filtered request failed, trying full import...')
                    params.pop('lastModStartDate', None)
                    try:
                        response = requests.get(base_url, params=params, headers=headers, timeout=30)
                        response.raise_for_status()
                        data = response.json()
                        last_mod_start_date = None  # Disable date filtering for subsequent requests
                    except requests.RequestException as e2:
                        raise Exception(f"API request failed: {e2}")
                else:
                    raise Exception(f"API request failed: {e}")
            
            if total_results is None:
                total_results = data.get('totalResults', 0)
                self.stdout.write(f'Total results: {total_results}')
            
            vulnerabilities = data.get('vulnerabilities', [])
            if not vulnerabilities:
                break
            
            self.process_cve_batch(vulnerabilities, import_log)
            
            start_index += len(vulnerabilities)
            
            # Check if we've processed all results
            if start_index >= total_results:
                break
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
    
    def process_cve_batch(self, vulnerabilities, import_log):
        """Process a batch of CVE vulnerabilities."""
        with transaction.atomic():
            for vuln_data in vulnerabilities:
                cve_data = vuln_data.get('cve', {})
                
                cve_id = cve_data.get('id')
                if not cve_id:
                    continue
                
                # Parse dates
                published_str = cve_data.get('published')
                last_modified_str = cve_data.get('lastModified')
                
                published = timezone.make_aware(datetime.fromisoformat(published_str.replace('Z', ''))) if published_str else timezone.now()
                last_modified = timezone.make_aware(datetime.fromisoformat(last_modified_str.replace('Z', ''))) if last_modified_str else timezone.now()
                
                # Get description
                descriptions = cve_data.get('descriptions', [])
                description = ''
                for desc in descriptions:
                    if desc.get('lang') == 'en':
                        description = desc.get('value', '')
                        break
                
                # Get or create CVE
                cve, created = CVE.objects.get_or_create(
                    cve_id=cve_id,
                    defaults={
                        'source_identifier': cve_data.get('sourceIdentifier', ''),
                        'published': published,
                        'last_modified': last_modified,
                        'vuln_status': cve_data.get('vulnStatus', ''),
                        'description': description,
                    }
                )
                
                # Update CVE if it exists and was modified
                updated = False
                if not created:
                    if cve.last_modified != last_modified:
                        cve.source_identifier = cve_data.get('sourceIdentifier', '')
                        cve.published = published
                        cve.last_modified = last_modified
                        cve.vuln_status = cve_data.get('vulnStatus', '')
                        cve.description = description
                        cve.save()
                        updated = True
                
                # Process CVSS metrics, references, weaknesses, and configurations
                if created or updated:
                    try:
                        self.process_cvss_metrics(cve, cve_data.get('metrics', {}))
                        self.process_references(cve, cve_data.get('references', []))
                        self.process_weaknesses(cve, cve_data.get('weaknesses', []))
                        self.process_configurations(cve, cve_data.get('configurations', []))
                    except Exception as e:
                        logger.warning(f"Failed to process related data for {cve_id}: {e}")
                        # Continue processing other CVEs even if one fails
                
                # Update counters
                import_log.records_processed += 1
                if created:
                    import_log.records_created += 1
                elif updated:
                    import_log.records_updated += 1
            
            import_log.save()
    
    def process_cvss_metrics(self, cve, metrics_data):
        """Process CVSS metrics for a CVE."""
        # Clear existing metrics
        cve.cvss_metrics.all().delete()
        
        for version, metrics_list in metrics_data.items():
            for metric_data in metrics_list:
                cvss_data = metric_data.get('cvssData', {})
                source = metric_data.get('source', '')
                metric_type = metric_data.get('type', '')
                
                # Use get_or_create to avoid duplicates
                CVSSMetric.objects.get_or_create(
                    cve=cve,
                    source=source,
                    type=metric_type,
                    defaults={
                        'cvss_version': cvss_data.get('version', version),
                        'vector_string': cvss_data.get('vectorString', ''),
                        'base_score': cvss_data.get('baseScore', 0.0),
                        'base_severity': cvss_data.get('baseSeverity', ''),
                        'exploitability_score': metric_data.get('exploitabilityScore'),
                        'impact_score': metric_data.get('impactScore'),
                    }
                )
    
    def process_references(self, cve, references_data):
        """Process references for a CVE."""
        # Clear existing references
        cve.references.all().delete()
        
        for ref_data in references_data:
            url = ref_data.get('url', '')
            if url:
                # Use get_or_create to avoid duplicates
                CVEReference.objects.get_or_create(
                    cve=cve,
                    url=url,
                    defaults={
                        'source': ref_data.get('source', ''),
                        'tags': ref_data.get('tags', []),
                    }
                )
    
    def process_weaknesses(self, cve, weaknesses_data):
        """Process weaknesses for a CVE."""
        # Clear existing weaknesses
        cve.weaknesses.all().delete()
        
        for weakness_data in weaknesses_data:
            source = weakness_data.get('source', '')
            weakness_type = weakness_data.get('type', '')
            
            for desc in weakness_data.get('description', []):
                cwe_id = desc.get('value', '')
                if cwe_id:  # Only create if we have a CWE ID
                    CVEWeakness.objects.get_or_create(
                        cve=cve,
                        source=source,
                        cwe_id=cwe_id,
                        defaults={
                            'type': weakness_type,
                            'description': desc.get('value', ''),
                        }
                    )
    
    def process_configurations(self, cve, configurations_data):
        """Process configurations for a CVE."""
        # Clear existing configurations
        cve.configurations.all().delete()
        
        for config_data in configurations_data:
            config = CVEConfiguration.objects.create(
                cve=cve,
                operator=config_data.get('operator', 'OR'),
                negate=config_data.get('negate', False),
            )
            
            for node_data in config_data.get('nodes', []):
                CVEConfigurationNode.objects.create(
                    configuration=config,
                    operator=node_data.get('operator', 'OR'),
                    negate=node_data.get('negate', False),
                    cpe_match=node_data.get('cpeMatch', []),
                )
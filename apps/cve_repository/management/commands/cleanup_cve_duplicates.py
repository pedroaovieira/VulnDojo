from django.core.management.base import BaseCommand
from django.db import transaction
from apps.cve_repository.models import CVE, CVSSMetric, CVEReference, CVEWeakness


class Command(BaseCommand):
    help = 'Clean up duplicate CVE-related records'
    
    def handle(self, *args, **options):
        self.stdout.write("Cleaning up duplicate CVE records...")
        
        with transaction.atomic():
            # Clean up duplicate CVSS metrics
            duplicates_removed = 0
            
            # Find and remove duplicate CVSS metrics
            seen_metrics = set()
            for metric in CVSSMetric.objects.all():
                key = (metric.cve_id, metric.source, metric.type)
                if key in seen_metrics:
                    metric.delete()
                    duplicates_removed += 1
                else:
                    seen_metrics.add(key)
            
            self.stdout.write(f"Removed {duplicates_removed} duplicate CVSS metrics")
            
            # Clean up duplicate references
            duplicates_removed = 0
            seen_refs = set()
            for ref in CVEReference.objects.all():
                key = (ref.cve_id, ref.url)
                if key in seen_refs:
                    ref.delete()
                    duplicates_removed += 1
                else:
                    seen_refs.add(key)
            
            self.stdout.write(f"Removed {duplicates_removed} duplicate references")
            
            # Clean up duplicate weaknesses
            duplicates_removed = 0
            seen_weaknesses = set()
            for weakness in CVEWeakness.objects.all():
                key = (weakness.cve_id, weakness.source, weakness.cwe_id)
                if key in seen_weaknesses:
                    weakness.delete()
                    duplicates_removed += 1
                else:
                    seen_weaknesses.add(key)
            
            self.stdout.write(f"Removed {duplicates_removed} duplicate weaknesses")
        
        self.stdout.write(
            self.style.SUCCESS("Successfully cleaned up duplicate records")
        )
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base model with common fields for all models."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class ImportLog(BaseModel):
    """Track import/update operations."""
    IMPORT_TYPES = [
        ('cpe', 'CPE Import'),
        ('cve', 'CVE Import'),
        ('linux_cve', 'Linux CVE Announcements'),
    ]
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]
    
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_import_type_display()} - {self.status} ({self.started_at})"
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()
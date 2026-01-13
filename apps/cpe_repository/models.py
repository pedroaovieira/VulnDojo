from django.db import models
from apps.core.models import BaseModel


class CPE(BaseModel):
    """Common Platform Enumeration model."""
    cpe_name = models.CharField(max_length=500, unique=True, db_index=True)
    cpe_name_id = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.TextField(blank=True)
    deprecated = models.BooleanField(default=False)
    deprecated_by = models.JSONField(default=list, blank=True)
    last_modified = models.DateTimeField()
    
    class Meta:
        ordering = ['cpe_name']
        indexes = [
            models.Index(fields=['cpe_name']),
            models.Index(fields=['deprecated']),
            models.Index(fields=['last_modified']),
        ]
    
    def __str__(self):
        return self.cpe_name
    
    @property
    def vendor(self):
        """Extract vendor from CPE name."""
        parts = self.cpe_name.split(':')
        return parts[3] if len(parts) > 3 else ''
    
    @property
    def product(self):
        """Extract product from CPE name."""
        parts = self.cpe_name.split(':')
        return parts[4] if len(parts) > 4 else ''
    
    @property
    def version(self):
        """Extract version from CPE name."""
        parts = self.cpe_name.split(':')
        return parts[5] if len(parts) > 5 else ''


class CPEReference(BaseModel):
    """References associated with CPE entries."""
    cpe = models.ForeignKey(CPE, on_delete=models.CASCADE, related_name='references')
    href = models.URLField()
    text = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['cpe', 'href']
    
    def __str__(self):
        return f"{self.cpe.cpe_name} - {self.href}"
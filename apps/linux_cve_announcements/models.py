from django.db import models
from apps.core.models import BaseModel
import re


class LinuxCVEAnnouncement(BaseModel):
    """Linux CVE Announcement from the mailing list."""
    message_id = models.CharField(max_length=200, unique=True, db_index=True)
    subject = models.CharField(max_length=500)
    sender = models.EmailField()
    date = models.DateTimeField()
    content = models.TextField()
    raw_content = models.TextField()  # Store original email content
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['date']),
            models.Index(fields=['sender']),
        ]
    
    def __str__(self):
        return f"{self.subject} ({self.date})"
    
    @property
    def cve_ids(self):
        """Extract CVE IDs from the announcement."""
        cve_pattern = r'CVE-\d{4}-\d{4,}'
        return re.findall(cve_pattern, self.content)
    
    @property
    def affected_components(self):
        """Extract affected components/subsystems."""
        # Simple extraction - could be enhanced with more sophisticated parsing
        lines = self.content.split('\n')
        components = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Component:') or line.startswith('Subsystem:'):
                component = line.split(':', 1)[1].strip()
                if component:
                    components.append(component)
        
        return components
    
    @property
    def severity(self):
        """Extract severity information if available."""
        severity_keywords = ['critical', 'high', 'medium', 'low']
        content_lower = self.content.lower()
        
        for severity in severity_keywords:
            if severity in content_lower:
                return severity.upper()
        
        return 'UNKNOWN'


class LinuxCVEAnnouncementCVE(BaseModel):
    """Many-to-many relationship between announcements and CVE IDs."""
    announcement = models.ForeignKey(
        LinuxCVEAnnouncement, 
        on_delete=models.CASCADE, 
        related_name='cve_references'
    )
    cve_id = models.CharField(max_length=20, db_index=True)
    
    class Meta:
        unique_together = ['announcement', 'cve_id']
        indexes = [
            models.Index(fields=['cve_id']),
        ]
    
    def __str__(self):
        return f"{self.announcement.subject} - {self.cve_id}"
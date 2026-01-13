from django.db import models
from apps.core.models import BaseModel


class CVE(BaseModel):
    """Common Vulnerabilities and Exposures model."""
    cve_id = models.CharField(max_length=20, unique=True, db_index=True)
    source_identifier = models.CharField(max_length=100, blank=True)
    published = models.DateTimeField()
    last_modified = models.DateTimeField()
    vuln_status = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    
    class Meta:
        ordering = ['-published']
        indexes = [
            models.Index(fields=['cve_id']),
            models.Index(fields=['published']),
            models.Index(fields=['last_modified']),
            models.Index(fields=['vuln_status']),
        ]
    
    def __str__(self):
        return self.cve_id
    
    @property
    def severity(self):
        """Get the highest severity from CVSS metrics."""
        cvss_metrics = self.cvss_metrics.all()
        if not cvss_metrics:
            return 'Unknown'
        
        severities = [metric.base_severity for metric in cvss_metrics if metric.base_severity]
        if not severities:
            return 'Unknown'
        
        # Order by severity (Critical > High > Medium > Low)
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        return max(severities, key=lambda x: severity_order.get(x, 0))


class CVSSMetric(BaseModel):
    """CVSS metrics for CVE entries."""
    cve = models.ForeignKey(CVE, on_delete=models.CASCADE, related_name='cvss_metrics')
    source = models.CharField(max_length=100)
    type = models.CharField(max_length=20)  # Primary, Secondary
    cvss_version = models.CharField(max_length=10)
    vector_string = models.CharField(max_length=200)
    base_score = models.FloatField()
    base_severity = models.CharField(max_length=20)
    exploitability_score = models.FloatField(null=True, blank=True)
    impact_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['cve', 'source', 'type']
    
    def __str__(self):
        return f"{self.cve.cve_id} - {self.cvss_version} - {self.base_score}"


class CVEReference(BaseModel):
    """References associated with CVE entries."""
    cve = models.ForeignKey(CVE, on_delete=models.CASCADE, related_name='references')
    url = models.URLField()
    source = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        unique_together = ['cve', 'url']
    
    def __str__(self):
        return f"{self.cve.cve_id} - {self.url}"


class CVEWeakness(BaseModel):
    """Weakness information for CVE entries."""
    cve = models.ForeignKey(CVE, on_delete=models.CASCADE, related_name='weaknesses')
    source = models.CharField(max_length=100)
    type = models.CharField(max_length=20)  # Primary, Secondary
    cwe_id = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['cve', 'source', 'cwe_id']
    
    def __str__(self):
        return f"{self.cve.cve_id} - {self.cwe_id}"


class CVEConfiguration(BaseModel):
    """Configuration/affected products for CVE entries."""
    cve = models.ForeignKey(CVE, on_delete=models.CASCADE, related_name='configurations')
    operator = models.CharField(max_length=10, default='OR')  # AND, OR
    negate = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.cve.cve_id} - Config {self.id}"


class CVEConfigurationNode(BaseModel):
    """Individual configuration nodes."""
    configuration = models.ForeignKey(CVEConfiguration, on_delete=models.CASCADE, related_name='nodes')
    operator = models.CharField(max_length=10, default='OR')
    negate = models.BooleanField(default=False)
    cpe_match = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"Config {self.configuration.id} - Node {self.id}"
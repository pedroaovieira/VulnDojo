from rest_framework import serializers
from .models import CVE, CVSSMetric, CVEReference, CVEWeakness, CVEConfiguration, CVEConfigurationNode


class CVSSMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVSSMetric
        fields = [
            'source', 'type', 'cvss_version', 'vector_string',
            'base_score', 'base_severity', 'exploitability_score', 'impact_score'
        ]


class CVEReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVEReference
        fields = ['url', 'source', 'tags']


class CVEWeaknessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVEWeakness
        fields = ['source', 'type', 'cwe_id', 'description']


class CVEConfigurationNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVEConfigurationNode
        fields = ['operator', 'negate', 'cpe_match']


class CVEConfigurationSerializer(serializers.ModelSerializer):
    nodes = CVEConfigurationNodeSerializer(many=True, read_only=True)
    
    class Meta:
        model = CVEConfiguration
        fields = ['operator', 'negate', 'nodes']


class CVESerializer(serializers.ModelSerializer):
    cvss_metrics = CVSSMetricSerializer(many=True, read_only=True)
    references = CVEReferenceSerializer(many=True, read_only=True)
    weaknesses = CVEWeaknessSerializer(many=True, read_only=True)
    configurations = CVEConfigurationSerializer(many=True, read_only=True)
    severity = serializers.ReadOnlyField()
    
    class Meta:
        model = CVE
        fields = [
            'id', 'cve_id', 'source_identifier', 'published', 'last_modified',
            'vuln_status', 'description', 'severity', 'cvss_metrics',
            'references', 'weaknesses', 'configurations', 'created_at', 'updated_at'
        ]


class CVEListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    severity = serializers.ReadOnlyField()
    base_score = serializers.SerializerMethodField()
    
    class Meta:
        model = CVE
        fields = [
            'id', 'cve_id', 'published', 'last_modified',
            'vuln_status', 'description', 'severity', 'base_score'
        ]
    
    def get_base_score(self, obj):
        """Get the highest base score from CVSS metrics."""
        metrics = obj.cvss_metrics.all()
        if not metrics:
            return None
        scores = [m.base_score for m in metrics if m.base_score]
        return max(scores) if scores else None
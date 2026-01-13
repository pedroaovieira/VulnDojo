from rest_framework import serializers
from .models import LinuxCVEAnnouncement, LinuxCVEAnnouncementCVE


class LinuxCVEAnnouncementCVESerializer(serializers.ModelSerializer):
    class Meta:
        model = LinuxCVEAnnouncementCVE
        fields = ['cve_id']


class LinuxCVEAnnouncementSerializer(serializers.ModelSerializer):
    cve_references = LinuxCVEAnnouncementCVESerializer(many=True, read_only=True)
    cve_ids = serializers.ReadOnlyField()
    affected_components = serializers.ReadOnlyField()
    severity = serializers.ReadOnlyField()
    
    class Meta:
        model = LinuxCVEAnnouncement
        fields = [
            'id', 'message_id', 'subject', 'sender', 'date', 'content',
            'cve_ids', 'affected_components', 'severity', 'cve_references',
            'created_at', 'updated_at'
        ]


class LinuxCVEAnnouncementListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    cve_ids = serializers.ReadOnlyField()
    severity = serializers.ReadOnlyField()
    
    class Meta:
        model = LinuxCVEAnnouncement
        fields = [
            'id', 'message_id', 'subject', 'sender', 'date',
            'cve_ids', 'severity'
        ]
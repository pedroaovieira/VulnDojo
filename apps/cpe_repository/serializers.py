from rest_framework import serializers
from .models import CPE, CPEReference


class CPEReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEReference
        fields = ['href', 'text']


class CPESerializer(serializers.ModelSerializer):
    references = CPEReferenceSerializer(many=True, read_only=True)
    vendor = serializers.ReadOnlyField()
    product = serializers.ReadOnlyField()
    version = serializers.ReadOnlyField()
    
    class Meta:
        model = CPE
        fields = [
            'id', 'cpe_name', 'cpe_name_id', 'title', 'deprecated',
            'deprecated_by', 'last_modified', 'vendor', 'product', 'version',
            'references', 'created_at', 'updated_at'
        ]


class CPEListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    vendor = serializers.ReadOnlyField()
    product = serializers.ReadOnlyField()
    version = serializers.ReadOnlyField()
    
    class Meta:
        model = CPE
        fields = [
            'id', 'cpe_name', 'title', 'deprecated',
            'vendor', 'product', 'version', 'last_modified'
        ]
from django.contrib import admin
from .models import CVE, CVSSMetric, CVEReference, CVEWeakness, CVEConfiguration, CVEConfigurationNode


class CVSSMetricInline(admin.TabularInline):
    model = CVSSMetric
    extra = 0


class CVEReferenceInline(admin.TabularInline):
    model = CVEReference
    extra = 0


class CVEWeaknessInline(admin.TabularInline):
    model = CVEWeakness
    extra = 0


@admin.register(CVE)
class CVEAdmin(admin.ModelAdmin):
    list_display = ['cve_id', 'published', 'last_modified', 'vuln_status', 'severity']
    list_filter = ['vuln_status', 'published', 'last_modified']
    search_fields = ['cve_id', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CVSSMetricInline, CVEReferenceInline, CVEWeaknessInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('cvss_metrics')


@admin.register(CVSSMetric)
class CVSSMetricAdmin(admin.ModelAdmin):
    list_display = ['cve', 'cvss_version', 'base_score', 'base_severity']
    list_filter = ['cvss_version', 'base_severity']
    search_fields = ['cve__cve_id']


@admin.register(CVEReference)
class CVEReferenceAdmin(admin.ModelAdmin):
    list_display = ['cve', 'url', 'source']
    search_fields = ['cve__cve_id', 'url']


@admin.register(CVEWeakness)
class CVEWeaknessAdmin(admin.ModelAdmin):
    list_display = ['cve', 'cwe_id', 'type']
    list_filter = ['type']
    search_fields = ['cve__cve_id', 'cwe_id']
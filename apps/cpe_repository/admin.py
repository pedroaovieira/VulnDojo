from django.contrib import admin
from .models import CPE, CPEReference


class CPEReferenceInline(admin.TabularInline):
    model = CPEReference
    extra = 0


@admin.register(CPE)
class CPEAdmin(admin.ModelAdmin):
    list_display = ['cpe_name', 'title', 'deprecated', 'last_modified']
    list_filter = ['deprecated', 'last_modified']
    search_fields = ['cpe_name', 'title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CPEReferenceInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('references')


@admin.register(CPEReference)
class CPEReferenceAdmin(admin.ModelAdmin):
    list_display = ['cpe', 'href', 'text']
    search_fields = ['cpe__cpe_name', 'href', 'text']
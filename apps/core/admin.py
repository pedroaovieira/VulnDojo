from django.contrib import admin
from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ['import_type', 'status', 'started_at', 'completed_at', 'records_processed']
    list_filter = ['import_type', 'status', 'started_at']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['import_type', 'error_message']
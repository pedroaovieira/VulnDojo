from django.contrib import admin
from .models import LinuxCVEAnnouncement, LinuxCVEAnnouncementCVE


class LinuxCVEAnnouncementCVEInline(admin.TabularInline):
    model = LinuxCVEAnnouncementCVE
    extra = 0


@admin.register(LinuxCVEAnnouncement)
class LinuxCVEAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'date', 'severity']
    list_filter = ['sender', 'date']
    search_fields = ['subject', 'content', 'message_id']
    readonly_fields = ['created_at', 'updated_at', 'cve_ids', 'affected_components', 'severity']
    inlines = [LinuxCVEAnnouncementCVEInline]
    
    fieldsets = (
        (None, {
            'fields': ('message_id', 'subject', 'sender', 'date')
        }),
        ('Content', {
            'fields': ('content', 'raw_content')
        }),
        ('Extracted Information', {
            'fields': ('cve_ids', 'affected_components', 'severity'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LinuxCVEAnnouncementCVE)
class LinuxCVEAnnouncementCVEAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'cve_id']
    search_fields = ['announcement__subject', 'cve_id']
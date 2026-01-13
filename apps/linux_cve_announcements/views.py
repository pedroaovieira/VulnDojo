from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import models
from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import LinuxCVEAnnouncement
from .serializers import LinuxCVEAnnouncementSerializer, LinuxCVEAnnouncementListSerializer


# API Views
class LinuxCVEAnnouncementListAPIView(generics.ListAPIView):
    """List Linux CVE announcements with search and filtering."""
    queryset = LinuxCVEAnnouncement.objects.all()
    serializer_class = LinuxCVEAnnouncementListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'content', 'sender']
    ordering_fields = ['date', 'subject']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by CVE ID
        cve_id = self.request.query_params.get('cve_id')
        if cve_id:
            queryset = queryset.filter(content__icontains=cve_id)
        
        # Filter by sender
        sender = self.request.query_params.get('sender')
        if sender:
            queryset = queryset.filter(sender__icontains=sender)
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(date__year=int(year))
        
        return queryset


class LinuxCVEAnnouncementDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a single Linux CVE announcement."""
    queryset = LinuxCVEAnnouncement.objects.all()
    serializer_class = LinuxCVEAnnouncementSerializer
    lookup_field = 'message_id'


@api_view(['GET'])
def linux_cve_stats(request):
    """Get Linux CVE announcements statistics."""
    total_announcements = LinuxCVEAnnouncement.objects.count()
    
    # Count by year
    year_counts = {}
    for announcement in LinuxCVEAnnouncement.objects.values('date__year').annotate(count=models.Count('id')):
        year_counts[announcement['date__year']] = announcement['count']
    
    # Top senders
    sender_counts = {}
    for announcement in LinuxCVEAnnouncement.objects.values('sender').annotate(count=models.Count('id')):
        sender_counts[announcement['sender']] = announcement['count']
    
    top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return Response({
        'total_announcements': total_announcements,
        'year_counts': year_counts,
        'top_senders': top_senders,
    })


# Web Views
def announcement_list(request):
    """Web interface for browsing Linux CVE announcements."""
    search_query = request.GET.get('search', '')
    sender_filter = request.GET.get('sender', '')
    year_filter = request.GET.get('year', '')
    
    announcements = LinuxCVEAnnouncement.objects.all()
    
    if search_query:
        announcements = announcements.filter(
            Q(subject__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    if sender_filter:
        announcements = announcements.filter(sender__icontains=sender_filter)
    
    if year_filter:
        announcements = announcements.filter(date__year=int(year_filter))
    
    paginator = Paginator(announcements, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available years for filter
    years = LinuxCVEAnnouncement.objects.dates('date', 'year', order='DESC')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sender_filter': sender_filter,
        'year_filter': year_filter,
        'years': years,
        'page_title': 'Linux CVE Announcements',
    }
    
    return render(request, 'linux_cve_announcements/announcement_list.html', context)


def announcement_detail(request, message_id):
    """Web interface for announcement detail view."""
    announcement = get_object_or_404(LinuxCVEAnnouncement, message_id=message_id)
    
    context = {
        'announcement': announcement,
        'page_title': f'Announcement: {announcement.subject}',
    }
    
    return render(request, 'linux_cve_announcements/announcement_detail.html', context)
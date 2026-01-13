from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Max, Count
from django.db import models
from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CVE
from .serializers import CVESerializer, CVEListSerializer


# API Views
class CVEListAPIView(generics.ListAPIView):
    """List CVE entries with search and filtering."""
    queryset = CVE.objects.all()
    serializer_class = CVEListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cve_id', 'description']
    ordering_fields = ['cve_id', 'published', 'last_modified']
    ordering = ['-published']
    
    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('cvss_metrics')
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            # This is a simplified filter - in production you might want more sophisticated filtering
            queryset = queryset.filter(cvss_metrics__base_severity__iexact=severity).distinct()
        
        # Filter by CVSS score range
        min_score = self.request.query_params.get('min_score')
        max_score = self.request.query_params.get('max_score')
        if min_score:
            queryset = queryset.filter(cvss_metrics__base_score__gte=float(min_score)).distinct()
        if max_score:
            queryset = queryset.filter(cvss_metrics__base_score__lte=float(max_score)).distinct()
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(published__year=int(year))
        
        return queryset


class CVEDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a single CVE entry."""
    queryset = CVE.objects.all()
    serializer_class = CVESerializer
    lookup_field = 'cve_id'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'cvss_metrics', 'references', 'weaknesses', 'configurations__nodes'
        )


@api_view(['GET'])
def cve_stats(request):
    """Get CVE repository statistics."""
    total_cves = CVE.objects.count()
    
    # Count by severity
    severity_counts = {}
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        count = CVE.objects.filter(cvss_metrics__base_severity=severity).distinct().count()
        severity_counts[severity.lower()] = count
    
    # Count by year
    year_counts = {}
    for cve in CVE.objects.values('published__year').annotate(count=models.Count('id')):
        year_counts[cve['published__year']] = cve['count']
    
    return Response({
        'total_cves': total_cves,
        'severity_counts': severity_counts,
        'year_counts': year_counts,
    })


# Web Views
def cve_list(request):
    """Web interface for browsing CVE entries."""
    search_query = request.GET.get('search', '')
    severity_filter = request.GET.get('severity', '')
    year_filter = request.GET.get('year', '')
    
    cves = CVE.objects.all().prefetch_related('cvss_metrics')
    
    if search_query:
        cves = cves.filter(
            Q(cve_id__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if severity_filter:
        cves = cves.filter(cvss_metrics__base_severity__iexact=severity_filter).distinct()
    
    if year_filter:
        cves = cves.filter(published__year=int(year_filter))
    
    paginator = Paginator(cves, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available years for filter
    years = CVE.objects.dates('published', 'year', order='DESC')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'severity_filter': severity_filter,
        'year_filter': year_filter,
        'years': years,
        'severities': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        'page_title': 'CVE Repository',
    }
    
    return render(request, 'cve_repository/cve_list.html', context)


def cve_detail(request, cve_id):
    """Web interface for CVE detail view."""
    cve = get_object_or_404(
        CVE.objects.prefetch_related(
            'cvss_metrics', 'references', 'weaknesses', 'configurations__nodes'
        ),
        cve_id=cve_id
    )
    
    context = {
        'cve': cve,
        'page_title': f'CVE: {cve.cve_id}',
    }
    
    return render(request, 'cve_repository/cve_detail.html', context)
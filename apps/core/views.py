from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ImportLog


def dashboard(request):
    """Main dashboard view."""
    # Import statistics
    recent_imports = ImportLog.objects.filter(
        started_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-started_at')[:10]
    
    # Get counts from each app
    context = {
        'recent_imports': recent_imports,
        'page_title': 'Dashboard',
    }
    
    # Try to get counts from each repository app
    try:
        from apps.cpe_repository.models import CPE
        context['cpe_count'] = CPE.objects.count()
    except ImportError:
        context['cpe_count'] = 0
    
    try:
        from apps.cve_repository.models import CVE
        context['cve_count'] = CVE.objects.count()
    except ImportError:
        context['cve_count'] = 0
    
    try:
        from apps.linux_cve_announcements.models import LinuxCVEAnnouncement
        context['linux_cve_count'] = LinuxCVEAnnouncement.objects.count()
    except ImportError:
        context['linux_cve_count'] = 0
    
    return render(request, 'core/dashboard.html', context)


def search(request):
    """Global search across all repositories."""
    query = request.GET.get('q', '')
    results = {
        'cpe': [],
        'cve': [],
        'linux_cve': [],
    }
    
    if query:
        # Search CPE
        try:
            from apps.cpe_repository.models import CPE
            results['cpe'] = CPE.objects.filter(
                Q(cpe_name__icontains=query) |
                Q(title__icontains=query)
            )[:10]
        except ImportError:
            pass
        
        # Search CVE
        try:
            from apps.cve_repository.models import CVE
            results['cve'] = CVE.objects.filter(
                Q(cve_id__icontains=query) |
                Q(description__icontains=query)
            )[:10]
        except ImportError:
            pass
        
        # Search Linux CVE Announcements
        try:
            from apps.linux_cve_announcements.models import LinuxCVEAnnouncement
            results['linux_cve'] = LinuxCVEAnnouncement.objects.filter(
                Q(subject__icontains=query) |
                Q(content__icontains=query)
            )[:10]
        except ImportError:
            pass
    
    context = {
        'query': query,
        'results': results,
        'page_title': 'Search Results',
    }
    
    return render(request, 'core/search.html', context)
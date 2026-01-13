from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CPE
from .serializers import CPESerializer, CPEListSerializer


# API Views
class CPEListAPIView(generics.ListAPIView):
    """List CPE entries with search and filtering."""
    queryset = CPE.objects.all()
    serializer_class = CPEListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cpe_name', 'title']
    ordering_fields = ['cpe_name', 'last_modified']
    ordering = ['cpe_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by deprecated status
        deprecated = self.request.query_params.get('deprecated')
        if deprecated is not None:
            queryset = queryset.filter(deprecated=deprecated.lower() == 'true')
        
        # Filter by vendor
        vendor = self.request.query_params.get('vendor')
        if vendor:
            queryset = queryset.filter(cpe_name__icontains=f':{vendor}:')
        
        # Filter by product
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(cpe_name__icontains=f':{product}:')
        
        return queryset


class CPEDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a single CPE entry."""
    queryset = CPE.objects.all()
    serializer_class = CPESerializer
    lookup_field = 'cpe_name_id'


@api_view(['GET'])
def cpe_stats(request):
    """Get CPE repository statistics."""
    total_cpes = CPE.objects.count()
    deprecated_cpes = CPE.objects.filter(deprecated=True).count()
    
    # Get top vendors
    vendors = {}
    for cpe in CPE.objects.all()[:1000]:  # Limit for performance
        vendor = cpe.vendor
        if vendor:
            vendors[vendor] = vendors.get(vendor, 0) + 1
    
    top_vendors = sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return Response({
        'total_cpes': total_cpes,
        'deprecated_cpes': deprecated_cpes,
        'active_cpes': total_cpes - deprecated_cpes,
        'top_vendors': top_vendors,
    })


# Web Views
def cpe_list(request):
    """Web interface for browsing CPE entries."""
    search_query = request.GET.get('search', '')
    deprecated_filter = request.GET.get('deprecated', '')
    vendor_filter = request.GET.get('vendor', '')
    
    cpes = CPE.objects.all()
    
    if search_query:
        cpes = cpes.filter(
            Q(cpe_name__icontains=search_query) |
            Q(title__icontains=search_query)
        )
    
    if deprecated_filter:
        cpes = cpes.filter(deprecated=deprecated_filter == 'true')
    
    if vendor_filter:
        cpes = cpes.filter(cpe_name__icontains=f':{vendor_filter}:')
    
    paginator = Paginator(cpes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'deprecated_filter': deprecated_filter,
        'vendor_filter': vendor_filter,
        'page_title': 'CPE Repository',
    }
    
    return render(request, 'cpe_repository/cpe_list.html', context)


def cpe_detail(request, cpe_name_id):
    """Web interface for CPE detail view."""
    cpe = get_object_or_404(CPE, cpe_name_id=cpe_name_id)
    
    context = {
        'cpe': cpe,
        'page_title': f'CPE: {cpe.cpe_name}',
    }
    
    return render(request, 'cpe_repository/cpe_detail.html', context)
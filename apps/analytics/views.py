from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    """Analytics dashboard view"""
    context = {
        'user': request.user,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def reports_view(request):
    """Reports view"""
    context = {
        'user': request.user,
    }
    return render(request, 'analytics/reports.html', context)

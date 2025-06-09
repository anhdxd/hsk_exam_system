from django.contrib import admin
from .models import HSKLevel


@admin.register(HSKLevel)
class HSKLevelAdmin(admin.ModelAdmin):
    """Admin configuration for HSKLevel model"""
    list_display = ('level', 'name', 'vocabulary_count', 'description')
    list_filter = ('level',)
    search_fields = ('name', 'description')
    ordering = ('level',)
    
    fieldsets = (
        ('Level Information', {
            'fields': ('level', 'name', 'vocabulary_count')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )

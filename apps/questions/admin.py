from django.contrib import admin
from .models import QuestionType, Question, Choice, QuestionBank


class ChoiceInline(admin.TabularInline):
    """Inline admin for choices"""
    model = Choice
    extra = 4
    min_num = 2
    fields = ('choice_text', 'is_correct', 'order')
    ordering = ('order',)


@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionType model"""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for Question model"""
    list_display = ('question_text_short', 'question_type', 'hsk_level', 'difficulty', 'points', 'is_active', 'created_at')
    list_filter = ('question_type', 'hsk_level', 'difficulty', 'is_active', 'created_at')
    search_fields = ('question_text', 'explanation')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChoiceInline]
    
    fieldsets = (
        ('Question Information', {
            'fields': ('question_text', 'question_type', 'hsk_level', 'difficulty', 'points')
        }),
        ('Additional Content', {
            'fields': ('passage', 'audio_file'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('explanation', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_text_short(self, obj):
        """Shortened question text for list display"""
        return obj.question_text[:75] + '...' if len(obj.question_text) > 75 else obj.question_text
    question_text_short.short_description = 'Question Text'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question_type', 'hsk_level')


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """Admin configuration for Choice model"""
    list_display = ('choice_text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'question__hsk_level', 'question__question_type')
    search_fields = ('choice_text', 'question__question_text')
    ordering = ('question', 'order')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question', 'question__hsk_level')


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    """Admin configuration for QuestionBank model"""
    list_display = ('name', 'hsk_level', 'question_count', 'is_active', 'created_at')
    list_filter = ('hsk_level', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'question_count')
    filter_horizontal = ('questions',)
    
    fieldsets = (
        ('Bank Information', {
            'fields': ('name', 'description', 'hsk_level', 'is_active')
        }),
        ('Questions', {
            'fields': ('questions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'question_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hsk_level').prefetch_related('questions')

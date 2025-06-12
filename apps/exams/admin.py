from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Exam, ExamSession, ExamAnswer


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """Admin configuration for Exam model"""
    list_display = ('title', 'hsk_level', 'total_questions',
                    'duration_minutes', 'passing_score', 'is_active', 'created_at')
    list_filter = ('hsk_level', 'is_active', 'allow_retake', 'allow_navigation',
                   'require_full_completion', 'show_results_immediately', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'hsk_level', 'question_bank')
        }),
        ('Exam Configuration', {
            'fields': ('duration_minutes', 'total_questions', 'passing_score')
        }),
        ('Availability', {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ('Settings', {
            'fields': ('randomize_questions', 'show_results_immediately', 'allow_retake', 'max_attempts')
        }),
        ('Instructions & Navigation', {
            'fields': ('instructions', 'allow_navigation', 'require_full_completion')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hsk_level', 'question_bank')


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    """Admin configuration for ExamSession model"""
    list_display = ('user', 'exam', 'status', 'percentage',
                    'passed', 'started_at', 'completed_at')
    list_filter = ('status', 'passed', 'exam__hsk_level',
                   'started_at', 'completed_at')
    search_fields = ('user__username', 'user__email', 'exam__title')
    readonly_fields = ('created_at', 'updated_at',
                       'percentage_display', 'exam_link')

    fieldsets = (
        ('Session Information', {
            'fields': ('exam_link', 'user', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'time_remaining')
        }),
        ('Results', {
            'fields': ('score', 'total_points', 'earned_points', 'percentage_display', 'passed')
        }),
        ('Session Data', {
            'fields': ('current_question_index', 'questions_order'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def percentage_display(self, obj):
        """Display percentage with color coding"""
        if obj.percentage is not None:
            color = 'green' if obj.passed else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color,
                obj.percentage
            )
        return '-'
    percentage_display.short_description = 'Percentage'

    def exam_link(self, obj):
        """Link to the exam in admin"""
        if obj.exam:
            url = reverse('admin:exams_exam_change', args=[obj.exam.pk])
            return format_html('<a href="{}">{}</a>', url, obj.exam.title)
        return '-'
    exam_link.short_description = 'Exam'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'exam', 'exam__hsk_level')


@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    """Admin configuration for ExamAnswer model"""
    list_display = ('exam_session', 'question', 'selected_choice', 
                    'is_correct', 'points_earned', 'time_spent_seconds')
    list_filter = ('is_correct', 'exam_session__exam__hsk_level',
                   'question__question_type', 'created_at')
    search_fields = ('exam_session__user__username', 'exam_session__exam__title', 
                     'question__question_text')
    readonly_fields = ('created_at', 'updated_at', 'is_correct', 'points_earned')

    fieldsets = (
        ('Answer Information', {
            'fields': ('exam_session', 'question', 'selected_choice', 'text_answer')
        }),
        ('Results', {
            'fields': ('is_correct', 'points_earned', 'time_spent_seconds')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'exam_session', 'exam_session__user', 'exam_session__exam',
            'question', 'selected_choice'
        )

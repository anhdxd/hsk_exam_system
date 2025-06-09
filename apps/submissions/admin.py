from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ExamAnswer


@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    """Admin configuration for ExamAnswer model"""
    list_display = ('exam_session_link', 'user', 'question_text_short', 'selected_choice_text', 'is_correct', 'points_earned', 'time_spent_display')
    list_filter = ('is_correct', 'exam_session__exam__hsk_level', 'question__question_type', 'created_at')
    search_fields = (
        'exam_session__user__username', 
        'exam_session__user__email',
        'question__question_text',
        'exam_session__exam__title'
    )
    readonly_fields = ('created_at', 'updated_at', 'is_correct_display', 'exam_session_link')
    
    fieldsets = (
        ('Answer Information', {
            'fields': ('exam_session_link', 'question', 'selected_choice', 'text_answer')
        }),
        ('Results', {
            'fields': ('is_correct_display', 'points_earned', 'time_spent_seconds')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user(self, obj):
        """Get user from exam session"""
        return obj.exam_session.user.username
    user.short_description = 'User'
    
    def question_text_short(self, obj):
        """Shortened question text"""
        text = obj.question.question_text
        return text[:50] + '...' if len(text) > 50 else text
    question_text_short.short_description = 'Question'
    
    def selected_choice_text(self, obj):
        """Display selected choice text"""
        if obj.selected_choice:
            return obj.selected_choice.choice_text[:30] + ('...' if len(obj.selected_choice.choice_text) > 30 else '')
        return obj.text_answer[:30] + ('...' if len(obj.text_answer) > 30 else '') if obj.text_answer else '-'
    selected_choice_text.short_description = 'Answer'
    
    def is_correct_display(self, obj):
        """Display correctness with color"""
        if obj.is_correct:
            return format_html('<span style="color: green; font-weight: bold;">✓ Correct</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Incorrect</span>')
    is_correct_display.short_description = 'Correctness'
    
    def exam_session_link(self, obj):
        """Link to exam session"""
        url = reverse('admin:exams_examsession_change', args=[obj.exam_session.pk])
        return format_html(
            '<a href="{}">{} - {}</a>', 
            url, 
            obj.exam_session.user.username,
            obj.exam_session.exam.title
        )
    exam_session_link.short_description = 'Exam Session'
    
    def time_spent_display(self, obj):
        """Display time spent in readable format"""
        if obj.time_spent_seconds:
            minutes, seconds = divmod(obj.time_spent_seconds, 60)
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return '-'
    time_spent_display.short_description = 'Time Spent'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'exam_session__user', 
            'exam_session__exam', 
            'question', 
            'selected_choice'
        )

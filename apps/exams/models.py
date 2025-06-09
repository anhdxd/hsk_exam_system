from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.common.models import TimeStampedModel, HSKLevel
from apps.questions.models import QuestionBank


class Exam(TimeStampedModel):
    """HSK Exam model"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    hsk_level = models.ForeignKey(HSKLevel, on_delete=models.CASCADE)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE)
    
    # Exam settings
    duration_minutes = models.IntegerField(default=120)
    total_questions = models.IntegerField(default=40)
    passing_score = models.FloatField(default=60.0, help_text="Passing score percentage")
    
    # Availability
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Settings
    randomize_questions = models.BooleanField(default=True)
    show_results_immediately = models.BooleanField(default=True)
    allow_retake = models.BooleanField(default=True)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
    
    def __str__(self):
        return f"{self.title} (HSK {self.hsk_level.level})"
    
    def is_available(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
    
    def get_duration_display(self):
        return f"{self.duration_minutes} minutes"


class ExamSession(TimeStampedModel):
    """Individual exam session for a user"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_remaining = models.IntegerField(null=True, blank=True, help_text="Minutes remaining")
    
    # Results
    score = models.FloatField(null=True, blank=True)
    total_points = models.IntegerField(default=0)
    earned_points = models.IntegerField(default=0)
    percentage = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    
    # Session data
    questions_order = models.JSONField(default=list, blank=True)
    current_question_index = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['exam', 'user', 'created_at']
        ordering = ['-created_at']
        verbose_name = 'Exam Session'
        verbose_name_plural = 'Exam Sessions'
    
    def __str__(self):
        return f"{self.user.username} - {self.exam.title} ({self.status})"
    
    def start_session(self):
        """Start the exam session"""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.time_remaining = self.exam.duration_minutes
            self.save()
    
    def complete_session(self):
        """Complete the exam session"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
    
    def is_expired(self):
        """Check if session has expired"""
        if self.started_at and self.exam.duration_minutes:
            expiry_time = self.started_at + timedelta(minutes=self.exam.duration_minutes)
            return timezone.now() > expiry_time
        return False
    
    def get_end_time(self):
        """Get the end time for this session"""
        if self.started_at:
            return self.started_at + timedelta(minutes=self.exam.duration_minutes)
        return None

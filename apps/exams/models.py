from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import json
import random

from apps.common.models import TimeStampedModel, HSKLevel
from apps.questions.models import QuestionBank, Question


class Exam(TimeStampedModel):
    """HSK Exam model"""
    title = models.CharField(
        max_length=200,
        verbose_name="Tiêu đề kỳ thi"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Mô tả"
    )
    hsk_level = models.ForeignKey(
        HSKLevel,
        on_delete=models.CASCADE,
        verbose_name="Cấp độ HSK"
    )
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        verbose_name="Ngân hàng câu hỏi"
    )

    # Exam settings
    duration_minutes = models.IntegerField(
        default=120,
        validators=[MinValueValidator(1), MaxValueValidator(480)],
        verbose_name="Thời gian thi (phút)"
    )
    total_questions = models.IntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        verbose_name="Tổng số câu hỏi"
    )
    passing_score = models.FloatField(
        default=60.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Điểm đậu (%)",
        verbose_name="Điểm đậu"
    )

    # Availability
    is_active = models.BooleanField(
        default=True,
        verbose_name="Kích hoạt"
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Ngày bắt đầu"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ngày kết thúc")

    # Settings
    randomize_questions = models.BooleanField(
        default=True,
        verbose_name="Xáo trộn câu hỏi"
    )
    show_results_immediately = models.BooleanField(
        default=True,
        verbose_name="Hiển thị kết quả ngay"
    )
    allow_retake = models.BooleanField(
        default=True,
        verbose_name="Cho phép thi lại"
    )
    max_attempts = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Số lần thi tối đa"
    )
    instructions = models.TextField(
        blank=True,
        verbose_name="Hướng dẫn thi",
        help_text="Hướng dẫn chi tiết cho thí sinh"
    )
    allow_navigation = models.BooleanField(
        default=True,
        verbose_name="Cho phép di chuyển giữa các câu",
        help_text="Cho phép thí sinh quay lại câu trước"
    )
    require_full_completion = models.BooleanField(
        default=False,
        verbose_name="Yêu cầu hoàn thành tất cả câu",
        help_text="Bắt buộc trả lời tất cả câu hỏi"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Kỳ thi'
        verbose_name_plural = 'Kỳ thi'
        indexes = [
            models.Index(fields=['hsk_level', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.title} (HSK {self.hsk_level.level})"

    def get_absolute_url(self):
        return reverse('exams:detail', kwargs={'pk': self.pk})

    def is_available(self):
        """Check if exam is available for taking"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def get_duration_display(self):
        """Get formatted duration"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"

    def get_available_questions(self):
        """Get questions available for this exam"""
        return self.question_bank.questions.filter(
            is_active=True,
            hsk_level=self.hsk_level
        ).select_related('question_type', 'hsk_level').prefetch_related('choices')

    def generate_question_order(self):
        """Generate random question order for exam"""
        questions = list(
            self.get_available_questions().values_list('id', flat=True))

        if self.randomize_questions:
            random.shuffle(questions)

        # Limit to total_questions
        return questions[:self.total_questions] 
    
    def can_user_take_exam(self, user):
        """Check if user can take this exam"""
        if not self.is_available():
            return False, "Kỳ thi không khả dụng"

        # Check attempt limit - only count completed and expired sessions
        completed_attempts = self.examsession_set.filter(
            user=user,
            status__in=['completed', 'expired']
        ).count()

        if completed_attempts >= self.max_attempts:
            return False, f"Bạn đã vượt quá số lần thi cho phép ({self.max_attempts})"

        # Check if user has an active session
        active_session = self.examsession_set.filter(
            user=user,
            status='in_progress'
        ).first()
        if active_session:
            if active_session.is_expired():
                active_session.status = 'expired'
                active_session.save()
            else:
                return False, "Bạn đang có phiên thi đang diễn ra"

        # Additional check for allow_retake - only prevent if user has passed
        if not self.allow_retake:
            passed_session = self.examsession_set.filter(
                user=user,
                status='completed',
                passed=True
            ).exists()
            if passed_session:
                return False, "Bạn đã hoàn thành kỳ thi này thành công"

        return True, "OK"


class ExamSession(TimeStampedModel):
    """Individual exam session for a user"""
    STATUS_CHOICES = [
        ('not_started', 'Chưa bắt đầu'),
        ('in_progress', 'Đang thi'),
        ('completed', 'Đã hoàn thành'),
        ('expired', 'Đã hết hạn'),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        verbose_name="Kỳ thi"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Thí sinh"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name="Trạng thái"
    )

    # Timing
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bắt đầu lúc"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Hoàn thành lúc"
    )
    time_remaining = models.IntegerField(
        null=True,
        blank=True,
        help_text="Thời gian còn lại (phút)",
        verbose_name="Thời gian còn lại"
    )

    # Results
    score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Điểm số"
    )
    total_points = models.IntegerField(
        default=0,
        verbose_name="Tổng điểm"
    )
    earned_points = models.IntegerField(
        default=0,
        verbose_name="Điểm đạt được"
    )
    percentage = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Phần trăm"
    )
    passed = models.BooleanField(
        default=False,
        verbose_name="Đã đậu")

    # Session data
    questions_order = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Thứ tự câu hỏi"
    )
    current_question_index = models.IntegerField(
        default=0,
        verbose_name="Chỉ số câu hỏi hiện tại"
    )
    user_answers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Câu trả lời của người dùng"
    )

    class Meta:
        unique_together = ['exam', 'user', 'created_at']
        ordering = ['-created_at']
        verbose_name = 'Phiên thi'
        verbose_name_plural = 'Phiên thi'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['exam', 'status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        if self.status == 'not_started':
            return reverse('exams:take', kwargs={'pk': self.exam.pk})
        elif self.status == 'in_progress':
            return reverse('exams:continue', kwargs={'pk': self.pk})
        else:
            return reverse('exams:result', kwargs={'pk': self.pk})

    def start_session(self):
        """Start the exam session"""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.time_remaining = self.exam.duration_minutes

            # Generate questions order if not already set
            if not self.questions_order:
                self.questions_order = self.exam.generate_question_order()

            self.save()
            return True
        return False

    def complete_session(self):
        """Complete the exam session and calculate results"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.calculate_results()
            self.save()
            return True
        return False

    def expire_session(self):
        """Expire the session due to time limit"""
        if self.status == 'in_progress':
            self.status = 'expired'
            self.completed_at = timezone.now()
            self.calculate_results()
            self.save()
            return True
        return False

    def is_expired(self):
        """Check if session has expired"""
        if self.started_at and self.exam.duration_minutes:
            expiry_time = self.started_at + \
                timedelta(minutes=self.exam.duration_minutes)
            return timezone.now() > expiry_time
        return False

    def get_end_time(self):
        """Get the end time for this session"""
        if self.started_at:
            return self.started_at + timedelta(minutes=self.exam.duration_minutes)
        return None

    def get_time_remaining_seconds(self):
        """Get remaining time in seconds"""
        if self.started_at and self.exam.duration_minutes:
            end_time = self.get_end_time()
            remaining = end_time - timezone.now()
            return max(0, int(remaining.total_seconds()))
        return 0

    def get_current_question(self):
        """Get the current question"""
        if self.questions_order and self.current_question_index < len(self.questions_order):
            question_id = self.questions_order[self.current_question_index]
            try:
                return Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                return None
        return None

    def has_next_question(self):
        """Check if there's a next question"""
        return self.current_question_index < len(self.questions_order) - 1

    def has_previous_question(self):
        """Check if there's a previous question"""
        return self.current_question_index > 0

    def get_progress_percentage(self):
        """Get progress percentage"""
        if self.questions_order:
            return (self.current_question_index / len(self.questions_order)) * 100
        return 0

    def save_answer(self, question_id, choice_id):
        """Save answer for a question"""
        self.user_answers[str(question_id)] = choice_id
        self.save(update_fields=['user_answers'])

    def get_answer(self, question_id):
        """Get saved answer for a question"""
        return self.user_answers.get(str(question_id))

    def calculate_results(self):
        """Calculate exam results"""
        total_points = 0
        earned_points = 0

        for question_id in self.questions_order:
            try:
                question = Question.objects.get(id=question_id)
                total_points += question.points

                # Check if answer is correct
                user_choice_id = self.get_answer(question_id)
                if user_choice_id:
                    correct_choice = question.choices.filter(
                        is_correct=True).first()
                    if correct_choice and str(correct_choice.id) == str(user_choice_id):
                        earned_points += question.points
            except Question.DoesNotExist:
                continue

        self.total_points = total_points
        self.earned_points = earned_points

        if total_points > 0:
            self.percentage = (earned_points / total_points) * 100
            self.passed = self.percentage >= self.exam.passing_score
        else:
            self.percentage = 0
            self.passed = False

        self.score = self.percentage

    def get_questions_with_answers(self):
        """Get all questions with user answers and correct answers"""
        questions_data = []

        for question_id in self.questions_order:
            try:
                question = Question.objects.get(id=question_id)
                user_choice_id = self.get_answer(question_id)
                user_choice = None
                correct_choice = question.choices.filter(
                    is_correct=True).first()

                if user_choice_id:
                    try:
                        user_choice = question.choices.get(id=user_choice_id)
                    except:
                        pass

                is_correct = (user_choice and
                              correct_choice and
                              user_choice.id == correct_choice.id)

                questions_data.append({
                    'question': question,
                    'user_choice': user_choice,
                    'correct_choice': correct_choice,
                    'is_correct': is_correct,
                    'points': question.points if is_correct else 0
                })
            except Question.DoesNotExist:
                continue

        return questions_data

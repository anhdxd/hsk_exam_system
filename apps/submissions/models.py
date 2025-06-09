from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel
from apps.exams.models import ExamSession
from apps.questions.models import Question, Choice


class ExamAnswer(TimeStampedModel):
    """User's answer to a specific question in an exam session"""
    exam_session = models.ForeignKey(
        ExamSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(
        Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(
        blank=True, help_text="For text-based questions")
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0.0)
    time_spent_seconds = models.IntegerField(
        default=0, help_text="Time spent on this question")

    class Meta:
        unique_together = ['exam_session', 'question']
        ordering = ['question__id']
        verbose_name = 'Exam Answer'
        verbose_name_plural = 'Exam Answers'

    def __str__(self):
        return f"{self.exam_session.user.username} - Q{self.question.id}: {'✓' if self.is_correct else '✗'}"

    def save(self, *args, **kwargs):
        """Auto-calculate if answer is correct"""
        if self.selected_choice and self.selected_choice.is_correct:
            self.is_correct = True
            self.points_earned = self.question.points
        else:
            self.is_correct = False
            self.points_earned = 0.0
        super().save(*args, **kwargs)

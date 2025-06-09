from django.db import models
from apps.common.models import TimeStampedModel, HSKLevel


class QuestionType(models.Model):
    """Types of HSK questions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Question Type'
        verbose_name_plural = 'Question Types'
    
    def __str__(self):
        return self.name


class Question(TimeStampedModel):
    """HSK Question model"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    question_text = models.TextField()
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE)
    hsk_level = models.ForeignKey(HSKLevel, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    
    # For reading comprehension questions
    passage = models.TextField(blank=True, help_text="Reading passage if applicable")
    
    # For listening questions
    audio_file = models.FileField(upload_to='questions/audio/', blank=True, null=True)
    
    # Metadata
    explanation = models.TextField(blank=True, help_text="Explanation of the correct answer")
    points = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['hsk_level', 'question_type', 'created_at']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
    
    def __str__(self):
        return f"HSK{self.hsk_level.level} - {self.question_type.name} - {self.question_text[:50]}..."


class Choice(models.Model):
    """Multiple choice options for questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'
    
    def __str__(self):
        return f"{self.choice_text} ({'✓' if self.is_correct else '✗'})"


class QuestionBank(TimeStampedModel):
    """Collection of questions for exam creation"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    hsk_level = models.ForeignKey(HSKLevel, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, related_name='question_banks')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Question Bank'
        verbose_name_plural = 'Question Banks'
    
    def __str__(self):
        return f"{self.name} (HSK {self.hsk_level.level})"
    
    def question_count(self):
        return self.questions.count()
    question_count.short_description = 'Questions'

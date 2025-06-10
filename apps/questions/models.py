from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
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
    """HSK Question model with comprehensive metadata and validation"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Dễ'),
        ('medium', 'Trung bình'),
        ('hard', 'Khó'),
    ]

    question_text = models.TextField(
        verbose_name="Câu hỏi",
        help_text="Nội dung câu hỏi"
    )
    question_type = models.ForeignKey(
        QuestionType,
        on_delete=models.CASCADE,
        verbose_name="Loại câu hỏi"
    )
    hsk_level = models.ForeignKey(
        HSKLevel,
        on_delete=models.CASCADE,
        verbose_name="Cấp độ HSK"
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name="Độ khó"
    )

    # For reading comprehension questions
    passage = models.TextField(
        blank=True,
        verbose_name="Đoạn văn",
        help_text="Đoạn văn đọc hiểu (nếu có)"
    )

    # For listening questions
    audio_file = models.FileField(
        upload_to='questions/audio/',
        blank=True,
        null=True,
        verbose_name="File âm thanh",
        help_text="File âm thanh cho câu hỏi nghe"
    )

    # Metadata
    explanation = models.TextField(
        blank=True,
        verbose_name="Giải thích",
        help_text="Giải thích đáp án đúng"
    )
    points = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Điểm số",
        help_text="Điểm số cho câu hỏi (1-10)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Kích hoạt"
    )

    # Add unique constraint to prevent duplicates
    class Meta:
        ordering = ['hsk_level', 'question_type', 'created_at']
        verbose_name = 'Câu hỏi'
        verbose_name_plural = 'Câu hỏi'
        indexes = [
            models.Index(fields=['hsk_level', 'question_type']),
            models.Index(fields=['is_active', 'hsk_level']),
        ]

    def __str__(self):
        return f"HSK{self.hsk_level.level} - {self.question_type.name} - {self.question_text[:50]}..."

    def get_absolute_url(self):
        return reverse('questions:detail', kwargs={'pk': self.pk})

    def get_correct_choice(self):
        """Get the correct choice for this question"""
        return self.choices.filter(is_correct=True).first()

    def get_choices(self):
        """Get all choices ordered by order field"""
        return self.choices.all().order_by('order')


class Choice(models.Model):
    """Multiple choice options for questions"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name="Câu hỏi"
    )
    choice_text = models.CharField(
        max_length=500,
        verbose_name="Lựa chọn",
        help_text="Nội dung lựa chọn"
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Đáp án đúng"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Thứ tự",
        help_text="Thứ tự hiển thị (A=0, B=1, C=2, D=3)"
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'Lựa chọn'
        verbose_name_plural = 'Lựa chọn'
        # Ensure only one correct answer per question
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'order'],
                name='unique_choice_order_per_question'
            )
        ]

    def __str__(self):
        return f"{self.choice_text} ({'✓' if self.is_correct else '✗'})"

    def get_choice_letter(self):
        """Return choice letter (A, B, C, D)"""
        letters = ['A', 'B', 'C', 'D', 'E', 'F']
        return letters[self.order] if self.order < len(letters) else str(self.order)


class QuestionBank(TimeStampedModel):
    """Collection of questions for exam creation"""
    name = models.CharField(
        max_length=200,
        verbose_name="Tên ngân hàng câu hỏi"
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
    questions = models.ManyToManyField(
        Question,
        related_name='question_banks',
        blank=True,
        verbose_name="Câu hỏi"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Kích hoạt"
    )

    class Meta:
        verbose_name = 'Ngân hàng câu hỏi'
        verbose_name_plural = 'Ngân hàng câu hỏi'
        # Prevent duplicate question banks for same level
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'hsk_level'],
                name='unique_questionbank_name_per_level'
            )
        ]

        def __str__(self):
            return f"{self.name} (HSK {self.hsk_level.level})"

    def get_absolute_url(self):
        return reverse('questions:banks_detail', kwargs={'pk': self.pk})

    def question_count(self):
        """Get total number of questions in this bank"""
        return self.questions.count()
    question_count.short_description = 'Số câu hỏi'

    def questions_by_type(self):
        """Get questions grouped by type"""
        from django.db.models import Count
        return self.questions.values('question_type__name').annotate(
            count=Count('id')
        ).order_by('question_type__name')

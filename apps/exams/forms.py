from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from .models import Exam, ExamSession
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank


class ExamForm(forms.ModelForm):
    """Form for creating and editing exams"""
    class Meta:
        model = Exam        
        fields = [
            'title', 'description', 'hsk_level', 'question_bank',
            'duration_minutes', 'total_questions', 'passing_score',
            'start_date', 'end_date', 'is_active',
            'randomize_questions', 'show_results_immediately',
            'allow_retake', 'max_attempts', 'instructions',
            'allow_navigation', 'require_full_completion'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề kỳ thi...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mô tả kỳ thi...'
            }),
            'hsk_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'question_bank': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 480
            }),
            'total_questions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 200
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.1
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'randomize_questions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_results_immediately': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_retake': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),            'max_attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Nhập hướng dẫn thi chi tiết...'
            }),
            'allow_navigation': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_full_completion': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter question banks by HSK level if instance exists
        if self.instance and self.instance.pk:
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(
                hsk_level=self.instance.hsk_level,
                is_active=True
            )
        else:
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(
                is_active=True
            ).select_related('hsk_level')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        hsk_level = cleaned_data.get('hsk_level')
        question_bank = cleaned_data.get('question_bank')
        total_questions = cleaned_data.get('total_questions')

        # Validate date range
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError({
                    'end_date': 'Ngày kết thúc phải sau ngày bắt đầu.'
                })

        # Validate question bank matches HSK level
        if hsk_level and question_bank:
            if question_bank.hsk_level != hsk_level:
                raise ValidationError({
                    'question_bank': 'Ngân hàng câu hỏi phải cùng cấp độ HSK.'
                })

        # Validate total questions vs available questions
        if question_bank and total_questions:
            available_count = question_bank.questions.filter(
                is_active=True,
                hsk_level=hsk_level
            ).count()

            if total_questions > available_count:
                raise ValidationError({
                    'total_questions': f'Chỉ có {available_count} câu hỏi khả dụng trong ngân hàng.'
                })

        return cleaned_data


class StartExamForm(forms.Form):
    """Form for starting an exam"""
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Tôi đã đọc và hiểu các quy định thi'
    )

    def __init__(self, exam, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam = exam
        self.user = user

    def clean_confirm(self):
        confirm = self.cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Bạn phải xác nhận đã đọc quy định thi.')
        return confirm

    def clean(self):
        cleaned_data = super().clean()

        # Check if user can take exam
        can_take, message = self.exam.can_user_take_exam(self.user)
        if not can_take:
            raise ValidationError(message)

        return cleaned_data


class ExamAnswerForm(forms.Form):
    """Form for submitting answers during exam"""
    choice = forms.ModelChoiceField(
        queryset=None,
        empty_label=None,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.fields['choice'].queryset = question.choices.all().order_by(
            'order')


class ExamSearchForm(forms.Form):
    """Form for searching and filtering exams"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm kỳ thi...'
        }),
        label='Tìm kiếm'
    )

    hsk_level = forms.ModelChoiceField(
        queryset=HSKLevel.objects.all().order_by('level'),
        required=False,
        empty_label='Tất cả cấp độ',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Cấp độ HSK'
    )

    status = forms.ChoiceField(
        choices=[
            ('', 'Tất cả trạng thái'),
            ('available', 'Khả dụng'),
            ('upcoming', 'Sắp diễn ra'),
            ('expired', 'Đã kết thúc'),
            ('inactive', 'Ngừng hoạt động'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Trạng thái'
    )


class ExamSessionFilterForm(forms.Form):
    """Form for filtering exam sessions"""
    user = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên người dùng...'
        }),
        label='Người dùng'
    )

    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all().order_by('-created_at'),
        required=False,
        empty_label='Tất cả kỳ thi',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Kỳ thi'
    )

    status = forms.ChoiceField(
        choices=[('', 'Tất cả trạng thái')] + ExamSession.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Trạng thái'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Từ ngày'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Đến ngày'
    )

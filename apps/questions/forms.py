from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Question, Choice, QuestionBank, QuestionType
from apps.common.models import HSKLevel


class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions"""

    class Meta:
        model = Question
        fields = [
            'question_text', 'question_type', 'hsk_level',
            'difficulty', 'passage', 'audio_file',
            'explanation', 'points', 'is_active'
        ]
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nhập nội dung câu hỏi...'
            }),
            'question_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hsk_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-control'
            }),
            'passage': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Nhập đoạn văn đọc hiểu (nếu có)...'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Giải thích đáp án đúng...'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['question_text'].required = True
        self.fields['question_type'].required = True
        self.fields['hsk_level'].required = True

        # Add help text
        self.fields['passage'].help_text = "Chỉ cần thiết cho câu hỏi đọc hiểu"
        self.fields['audio_file'].help_text = "Chỉ cần thiết cho câu hỏi nghe"

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        passage = cleaned_data.get('passage')
        audio_file = cleaned_data.get('audio_file')

        # Validate passage for reading comprehension
        if question_type and 'reading' in question_type.name.lower():
            if not passage:
                raise ValidationError({
                    'passage': 'Đoạn văn là bắt buộc cho câu hỏi đọc hiểu.'
                })

        # Validate audio for listening questions
        if question_type and 'listening' in question_type.name.lower():
            if not audio_file and not self.instance.pk:
                raise ValidationError({
                    'audio_file': 'File âm thanh là bắt buộc cho câu hỏi nghe.'
                })

        return cleaned_data


class ChoiceForm(forms.ModelForm):
    """Form for creating and editing choices"""

    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct', 'order']
        widgets = {
            'choice_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập nội dung lựa chọn...'
            }),
            'is_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 5
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['choice_text'].required = True


# Create formset for handling multiple choices
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,  # Default 4 choices (A, B, C, D)
    max_num=6,  # Maximum 6 choices
    min_num=2,  # Minimum 2 choices
    can_delete=True,
    validate_min=True,
    validate_max=True
)


class QuestionBankForm(forms.ModelForm):
    """Form for creating and editing question banks"""

    class Meta:
        model = QuestionBank
        fields = ['name', 'description', 'hsk_level', 'questions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên ngân hàng câu hỏi...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả ngân hàng câu hỏi...'
            }),
            'hsk_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'questions': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['hsk_level'].required = True

        # Filter questions by HSK level if editing
        if self.instance.pk and self.instance.hsk_level:
            self.fields['questions'].queryset = Question.objects.filter(
                hsk_level=self.instance.hsk_level,
                is_active=True
            )


class ImportForm(forms.Form):
    """Form for importing questions from CSV/JSON files"""

    FILE_TYPE_CHOICES = [
        ('csv', 'CSV File'),
        ('json', 'JSON File'),
    ]

    file_type = forms.ChoiceField(
        choices=FILE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Loại file"
    )

    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.json'
        }),
        label="Chọn file",
        help_text="Chọn file CSV hoặc JSON chứa câu hỏi"
    )

    hsk_level = forms.ModelChoiceField(
        queryset=HSKLevel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cấp độ HSK",
        help_text="Cấp độ HSK cho tất cả câu hỏi trong file"
    )

    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Ngân hàng câu hỏi (tùy chọn)",
        help_text="Thêm câu hỏi vào ngân hàng câu hỏi có sẵn"
    )

    create_new_bank = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Tạo ngân hàng câu hỏi mới"
    )

    new_bank_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên ngân hàng câu hỏi mới...'
        }),
        label="Tên ngân hàng mới",
        help_text="Chỉ cần khi tạo ngân hàng câu hỏi mới"
    )

    overwrite_duplicates = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Ghi đè câu hỏi trùng lặp",
        help_text="Có ghi đè những câu hỏi đã tồn tại không?"
    )

    def clean(self):
        cleaned_data = super().clean()
        file_type = cleaned_data.get('file_type')
        file = cleaned_data.get('file')
        create_new_bank = cleaned_data.get('create_new_bank')
        new_bank_name = cleaned_data.get('new_bank_name')
        question_bank = cleaned_data.get('question_bank')

        # Validate file extension
        if file and file_type:
            file_name = file.name.lower()
            if file_type == 'csv' and not file_name.endswith('.csv'):
                raise ValidationError({
                    'file': 'File phải có định dạng .csv'
                })
            elif file_type == 'json' and not file_name.endswith('.json'):
                raise ValidationError({
                    'file': 'File phải có định dạng .json'
                })

        # Validate new bank name if creating new bank
        if create_new_bank and not new_bank_name:
            raise ValidationError({
                'new_bank_name': 'Tên ngân hàng câu hỏi là bắt buộc khi tạo mới.'
            })

        # Must select either existing bank or create new one
        if not create_new_bank and not question_bank:
            raise ValidationError(
                'Bạn phải chọn ngân hàng câu hỏi có sẵn hoặc tạo ngân hàng mới.'
            )

        return cleaned_data


class QuestionSearchForm(forms.Form):
    """Form for searching and filtering questions"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm câu hỏi...'
        }),
        label="Tìm kiếm"
    )

    hsk_level = forms.ModelChoiceField(
        queryset=HSKLevel.objects.all(),
        required=False,
        empty_label="Tất cả cấp độ",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cấp độ HSK"
    )

    question_type = forms.ModelChoiceField(
        queryset=QuestionType.objects.all(),
        required=False,
        empty_label="Tất cả loại",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Loại câu hỏi"
    )

    difficulty = forms.ChoiceField(
        choices=[('', 'Tất cả độ khó')] + Question.DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Độ khó"
    )

    is_active = forms.ChoiceField(
        choices=[
            ('', 'Tất cả'),
            ('true', 'Kích hoạt'),
            ('false', 'Không kích hoạt')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Trạng thái"
    )


class QuestionBankSearchForm(forms.Form):
    """Form for searching and filtering question banks"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên ngân hàng...'
        }),
        label="Tìm kiếm"
    )

    hsk_level = forms.ModelChoiceField(
        queryset=HSKLevel.objects.all(),
        required=False,
        empty_label="Tất cả cấp độ",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cấp độ HSK"
    )

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Row, Column
from crispy_forms.bootstrap import Field
from .models import Profile

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with Vietnamese labels"""
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
            'class': 'form-control'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        label="Họ",
        widget=forms.TextInput(attrs={
            'placeholder': 'Nguyễn',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        label="Tên",
        widget=forms.TextInput(attrs={
            'placeholder': 'Văn A',
            'class': 'form-control'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Số điện thoại",
        widget=forms.TextInput(attrs={
            'placeholder': '+84 123 456 789',
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Thông tin cá nhân',
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'email',
                'phone_number',
            ),
            Fieldset(
                'Thông tin đăng nhập',
                'password1',
                'password2',
            ),
            ButtonHolder(
                Submit('submit', 'Đăng ký', css_class='btn btn-primary btn-lg btn-block')
            )
        )
        
        # Custom field labels and help texts
        self.fields['password1'].label = "Mật khẩu"
        self.fields['password1'].help_text = "Mật khẩu phải có ít nhất 8 ký tự và không được quá phổ biến."
        self.fields['password2'].label = "Xác nhận mật khẩu"
        self.fields['password2'].help_text = "Nhập lại mật khẩu để xác nhận."

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone_number = self.cleaned_data.get("phone_number", "")
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with Vietnamese labels"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', placeholder="Email của bạn"),
            Field('password', placeholder="Mật khẩu"),
            ButtonHolder(
                Submit('submit', 'Đăng nhập', css_class='btn btn-primary btn-lg btn-block')
            )
        )
        
        # Custom field labels
        self.fields['username'].label = "Email"
        self.fields['username'].widget.attrs.update({
            'placeholder': 'your.email@example.com',
            'class': 'form-control'
        })
        self.fields['password'].label = "Mật khẩu"
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Nhập mật khẩu',
            'class': 'form-control'
        })


class ProfileForm(forms.ModelForm):
    """Profile form for user profile editing"""
    
    class Meta:
        model = Profile
        fields = [
            'phone_number',
            'date_of_birth', 
            'chinese_level',
            'bio', 
            'avatar', 
            'target_hsk_level', 
            'study_hours_per_week',
            'city',
            'country',
            'preferred_study_time'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+84 123 456 789'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'chinese_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_hsk_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'study_hours_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'preferred_study_time': forms.Select(attrs={
                'class': 'form-control'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Hãy chia sẻ về bản thân bạn...'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hà Nội'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vietnam'
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Thông tin cá nhân',
                Row(
                    Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                    Column('chinese_level', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('city', css_class='form-group col-md-6 mb-0'),
                    Column('country', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'bio',
                'avatar',
            ),
            Fieldset(
                'Mục tiêu học tập',
                Row(
                    Column('target_hsk_level', css_class='form-group col-md-6 mb-0'),
                    Column('study_hours_per_week', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'preferred_study_time',
            ),
            ButtonHolder(
                Submit('submit', 'Cập nhật hồ sơ', css_class='btn btn-success btn-lg')
            )
        )


class UserForm(forms.ModelForm):
    """User form for editing basic user information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'email',
            'phone_number',
            ButtonHolder(
                Submit('submit', 'Cập nhật thông tin', css_class='btn btn-primary btn-lg')
            )
        )

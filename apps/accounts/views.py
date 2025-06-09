from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileForm, UserForm
from .models import CustomUser, Profile
from apps.exams.models import ExamSession


class CustomRegisterView(CreateView):
    """Custom registration view"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Chào mừng {form.cleaned_data["first_name"]}! Tài khoản của bạn đã được tạo thành công. Vui lòng đăng nhập.'
        )
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """Custom login view"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Chào mừng bạn quay trở lại, {self.request.user.get_full_name()}!'
        )
        return response


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Bạn đã đăng xuất thành công. Hẹn gặp lại!')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard_view(request):
    """User dashboard view"""
    user = request.user
    profile = user.profile
    
    # Get user's exam statistics
    exam_sessions = ExamSession.objects.filter(user=user)
    total_exams = exam_sessions.count()
    completed_exams = exam_sessions.filter(status='completed').count()
    
    # Calculate average score
    completed_sessions = exam_sessions.filter(status='completed', percentage__isnull=False)
    average_score = completed_sessions.aggregate(avg_score=Avg('percentage'))['avg_score']
    
    # Get recent exam sessions
    recent_sessions = exam_sessions.order_by('-created_at')[:5]
    
    # HSK level progress (mock data for now)
    hsk_progress = {
        'target_level': profile.target_hsk_level,
        'current_progress': min(completed_exams * 10, 100),  # Mock calculation
    }
    
    context = {
        'user': user,
        'profile': profile,
        'total_exams': total_exams,
        'completed_exams': completed_exams,
        'average_score': round(average_score, 1) if average_score else 0,
        'recent_sessions': recent_sessions,
        'hsk_progress': hsk_progress,
    }
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_edit_view(request):
    """Edit user profile"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Hồ sơ của bạn đã được cập nhật thành công!')
            return redirect('accounts:dashboard')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def profile_view(request):
    """View user profile"""
    user = request.user
    profile = user.profile
    
    # Get user's exam statistics
    exam_sessions = ExamSession.objects.filter(user=user)
    total_exams = exam_sessions.count()
    completed_exams = exam_sessions.filter(status='completed').count()
    
    # Get exam performance by HSK level
    hsk_performance = {}
    for level in range(1, 7):
        level_sessions = exam_sessions.filter(
            exam__hsk_level__level=level,
            status='completed',
            percentage__isnull=False
        )
        if level_sessions.exists():
            avg_score = level_sessions.aggregate(avg=Avg('percentage'))['avg']
            hsk_performance[f'HSK {level}'] = {
                'attempts': level_sessions.count(),
                'average_score': round(avg_score, 1) if avg_score else 0
            }
    
    context = {
        'user': user,
        'profile': profile,
        'total_exams': total_exams,
        'completed_exams': completed_exams,
        'hsk_performance': hsk_performance,
    }
    
    return render(request, 'accounts/profile.html', context)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Profile edit view using class-based view"""
    model = Profile
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_object(self):
        """Get the profile object for the current user"""
        return self.request.user.profile
    
    def get_context_data(self, **kwargs):
        """Add user form to context"""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = UserForm(self.request.POST, instance=self.request.user)
            context['profile_form'] = context['form']  # Use the form from parent class
        else:
            context['user_form'] = UserForm(instance=self.request.user)
            context['profile_form'] = context['form']  # Use the form from parent class
        return context
    
    def form_valid(self, form):
        """Handle form validation for both user and profile forms"""
        context = self.get_context_data()
        user_form = context['user_form']
        
        if user_form.is_valid():
            user_form.save()
            messages.success(self.request, 'Hồ sơ của bạn đã được cập nhật thành công!')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Có lỗi xảy ra khi cập nhật hồ sơ. Vui lòng kiểm tra lại thông tin.')
        return super().form_invalid(form)


# Function-based views for backward compatibility
def register_view(request):
    """Function-based register view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f'Chào mừng {form.cleaned_data["first_name"]}! Tài khoản của bạn đã được tạo thành công.'
            )
            # Automatically log in the user
            username = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('accounts:dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Function-based login view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(
                    request,
                    f'Chào mừng bạn quay trở lại, {user.get_full_name()}!'
                )
                return redirect('accounts:dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Function-based logout view"""
    if request.user.is_authenticated:
        messages.info(request, 'Bạn đã đăng xuất thành công. Hẹn gặp lại!')
    logout(request)
    return redirect('accounts:login')

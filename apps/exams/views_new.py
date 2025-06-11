from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
import json

from .models import Exam, ExamSession
from .forms import ExamForm, StartExamForm, ExamAnswerForm, ExamSearchForm, ExamSessionFilterForm
from apps.common.models import HSKLevel
from apps.questions.models import Question


class ExamListView(ListView):
    """List view for exams with search and filtering"""
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Exam.objects.select_related('hsk_level', 'question_bank')
        
        # Get search parameters
        search = self.request.GET.get('search')
        hsk_level = self.request.GET.get('hsk_level')
        status = self.request.GET.get('status')
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        if hsk_level:
            queryset = queryset.filter(hsk_level_id=hsk_level)
        
        # Filter by status
        now = timezone.now()
        if status == 'available':
            queryset = queryset.filter(
                is_active=True,
                start_date__lte=now
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            )
        elif status == 'upcoming':
            queryset = queryset.filter(
                is_active=True,
                start_date__gt=now
            )
        elif status == 'expired':
            queryset = queryset.filter(
                Q(is_active=False) | Q(end_date__lt=now)
            )
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ExamSearchForm(self.request.GET)
        context['total_exams'] = self.get_queryset().count()
        
        # Add user session info if authenticated
        if self.request.user.is_authenticated:
            context['user_sessions'] = ExamSession.objects.filter(
                user=self.request.user
            ).select_related('exam').order_by('-created_at')[:5]
        
        return context


class ExamDetailView(DetailView):
    """Detail view for a single exam"""
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.object
        
        # Add exam statistics
        context['total_sessions'] = exam.examsession_set.count()
        context['completed_sessions'] = exam.examsession_set.filter(
            status='completed'
        ).count()
        
        if context['completed_sessions'] > 0:
            context['average_score'] = exam.examsession_set.filter(
                status='completed'
            ).aggregate(avg_score=Avg('percentage'))['avg_score']
            context['pass_rate'] = (
                exam.examsession_set.filter(
                    status='completed', 
                    passed=True
                ).count() / context['completed_sessions']
            ) * 100
        
        # Add user-specific info if authenticated
        if self.request.user.is_authenticated:
            context['user_sessions'] = exam.examsession_set.filter(
                user=self.request.user
            ).order_by('-created_at')
            
            context['can_take_exam'], context['take_exam_message'] = exam.can_user_take_exam(
                self.request.user
            )
            
            # Check for active session
            context['active_session'] = exam.examsession_set.filter(
                user=self.request.user,
                status='in_progress'
            ).first()
        
        return context


class ExamCreateView(LoginRequiredMixin, CreateView):
    """Create view for exams"""
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Kỳ thi "{form.instance.title}" đã được tạo thành công!'
        )
        return super().form_valid(form)


class ExamUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for exams"""
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Kỳ thi "{form.instance.title}" đã được cập nhật!'
        )
        return super().form_valid(form)


class ExamDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for exams"""
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exams:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(
            request,
            f'Kỳ thi "{self.get_object().title}" đã được xóa!'
        )
        return super().delete(request, *args, **kwargs)


@login_required
def start_exam_view(request, pk):
    """Start a new exam session"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        form = StartExamForm(exam, request.user, request.POST)
        if form.is_valid():
            # Create new exam session
            session = ExamSession.objects.create(
                exam=exam,
                user=request.user
            )
            
            if session.start_session():
                messages.success(request, f'Bắt đầu thi "{exam.title}"')
                return redirect('exams:take_exam', pk=session.pk)
            else:
                messages.error(request, 'Không thể bắt đầu phiên thi.')
                return redirect('exams:detail', pk=exam.pk)
    else:
        form = StartExamForm(exam, request.user)
    
    return render(request, 'exams/start_exam.html', {
        'exam': exam,
        'form': form
    })


@login_required
def take_exam_view(request, pk):
    """Take exam view - main exam interface"""
    session = get_object_or_404(ExamSession, pk=pk, user=request.user)
    
    # Check session status
    if session.status == 'completed':
        return redirect('exams:result', pk=session.pk)
    elif session.status == 'expired':
        messages.warning(request, 'Phiên thi đã hết hạn.')
        return redirect('exams:result', pk=session.pk)
    elif session.status == 'not_started':
        return redirect('exams:start', pk=session.exam.pk)
    
    # Check if session expired
    if session.is_expired():
        session.expire_session()
        messages.warning(request, 'Thời gian thi đã hết.')
        return redirect('exams:result', pk=session.pk)
    
    # Get current question
    current_question = session.get_current_question()
    if not current_question:
        # No more questions, complete the exam
        session.complete_session()
        messages.success(request, 'Bạn đã hoàn thành bài thi!')
        return redirect('exams:result', pk=session.pk)
    
    # Handle form submission
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_answer':
            choice_id = request.POST.get('choice')
            if choice_id:
                session.save_answer(current_question.id, choice_id)
                messages.success(request, 'Đã lưu câu trả lời.')
        
        elif action == 'next':
            # Save answer if provided
            choice_id = request.POST.get('choice')
            if choice_id:
                session.save_answer(current_question.id, choice_id)
            
            # Move to next question
            if session.has_next_question():
                session.current_question_index += 1
                session.save(update_fields=['current_question_index'])
            else:
                # Complete exam
                session.complete_session()
                messages.success(request, 'Bạn đã hoàn thành bài thi!')
                return redirect('exams:result', pk=session.pk)
        
        elif action == 'previous':
            # Save answer if provided
            choice_id = request.POST.get('choice')
            if choice_id:
                session.save_answer(current_question.id, choice_id)
            
            # Move to previous question
            if session.has_previous_question():
                session.current_question_index -= 1
                session.save(update_fields=['current_question_index'])
        
        elif action == 'complete':
            # Save current answer
            choice_id = request.POST.get('choice')
            if choice_id:
                session.save_answer(current_question.id, choice_id)
            
            # Complete exam
            session.complete_session()
            messages.success(request, 'Bạn đã nộp bài thành công!')
            return redirect('exams:result', pk=session.pk)
        
        return redirect('exams:take_exam', pk=session.pk)
    
    # Prepare form for current question
    form = ExamAnswerForm(current_question)
    
    # Set initial value if user has already answered
    saved_answer = session.get_answer(current_question.id)
    if saved_answer:
        try:
            form.fields['choice'].initial = int(saved_answer)
        except (ValueError, TypeError):
            pass
    
    return render(request, 'exams/take_exam.html', {
        'session': session,
        'exam': session.exam,
        'question': current_question,
        'form': form,
        'question_number': session.current_question_index + 1,
        'total_questions': len(session.questions_order),
        'progress_percentage': session.get_progress_percentage(),
        'time_remaining_seconds': session.get_time_remaining_seconds(),
    })


@login_required
def exam_result_view(request, pk):
    """View exam results"""
    session = get_object_or_404(ExamSession, pk=pk, user=request.user)
    
    if session.status not in ['completed', 'expired']:
        messages.warning(request, 'Kết quả chưa khả dụng.')
        return redirect('exams:take_exam', pk=session.pk)
    
    # Get detailed results if exam shows results immediately
    questions_with_answers = []
    if session.exam.show_results_immediately:
        questions_with_answers = session.get_questions_with_answers()
    
    return render(request, 'exams/exam_result.html', {
        'session': session,
        'exam': session.exam,
        'questions_with_answers': questions_with_answers,
        'show_detailed_results': session.exam.show_results_immediately,
    })


@login_required
def continue_exam_view(request, pk):
    """Continue an existing exam session"""
    session = get_object_or_404(ExamSession, pk=pk, user=request.user)
    
    if session.status != 'in_progress':
        return redirect('exams:detail', pk=session.exam.pk)
    
    return redirect('exams:take_exam', pk=session.pk)


# Admin/Management Views
class ExamSessionListView(LoginRequiredMixin, ListView):
    """List view for exam sessions (admin/teacher view)"""
    model = ExamSession
    template_name = 'exams/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ExamSession.objects.select_related(
            'exam', 'user'
        ).order_by('-created_at')
        
        # Apply filters
        user_search = self.request.GET.get('user')
        exam_id = self.request.GET.get('exam')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if user_search:
            queryset = queryset.filter(
                Q(user__username__icontains=user_search) |
                Q(user__first_name__icontains=user_search) |
                Q(user__last_name__icontains=user_search)
            )
        
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ExamSessionFilterForm(self.request.GET)
        return context


# AJAX Views
@login_required
def exam_time_check(request, pk):
    """AJAX view to check remaining time"""
    session = get_object_or_404(ExamSession, pk=pk, user=request.user)
    
    if session.status != 'in_progress':
        return JsonResponse({'status': 'error', 'message': 'Phiên thi không hợp lệ'})
    
    time_remaining = session.get_time_remaining_seconds()
    
    if time_remaining <= 0:
        session.expire_session()
        return JsonResponse({
            'status': 'expired',
            'message': 'Hết thời gian thi',
            'redirect_url': reverse('exams:result', kwargs={'pk': session.pk})
        })
    
    return JsonResponse({
        'status': 'ok',
        'time_remaining': time_remaining
    })


@login_required
def save_answer_ajax(request, pk):
    """AJAX view to save answer"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'})
    
    session = get_object_or_404(ExamSession, pk=pk, user=request.user)
    
    if session.status != 'in_progress':
        return JsonResponse({'status': 'error', 'message': 'Phiên thi không hợp lệ'})
    
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        choice_id = data.get('choice_id')
        
        if question_id and choice_id:
            session.save_answer(question_id, choice_id)
            return JsonResponse({'status': 'success', 'message': 'Đã lưu câu trả lời'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'})
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Dữ liệu JSON không hợp lệ'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

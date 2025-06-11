from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Exam, ExamSession


def exam_list_view(request):
    """List all available exams"""
    exams = Exam.objects.filter(is_active=True)
    context = {
        'exams': exams,
    }
    return render(request, 'exams/exam_list.html', context)


def exam_detail_view(request, exam_id):
    """Exam detail view"""
    exam = get_object_or_404(Exam, id=exam_id)
    context = {
        'exam': exam,
    }
    return render(request, 'exams/exam_detail.html', context)


@login_required
def start_exam_view(request, exam_id):
    """Start a new exam session"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    if not exam.is_available():
        messages.error(request, 'Bài thi này hiện không khả dụng.')
        return redirect('exams:detail', exam_id=exam_id)
    
    # Create new exam session
    session = ExamSession.objects.create(
        exam=exam,
        user=request.user
    )
    session.start_session()
    
    return redirect('exams:take', session_id=session.id)


@login_required
def take_exam_view(request, session_id):
    """Take exam view"""
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    
    if session.status == 'completed':
        return redirect('exams:result', session_id=session_id)
    
    context = {
        'session': session,
        'exam': session.exam,
    }
    return render(request, 'exams/take_exam.html', context)


@login_required
def exam_result_view(request, session_id):
    """Exam result view"""
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    
    context = {
        'session': session,
        'exam': session.exam,
    }
    return render(request, 'exams/exam_result.html', context)

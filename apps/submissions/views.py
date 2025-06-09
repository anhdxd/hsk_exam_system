from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ExamAnswer
from apps.exams.models import Exam, ExamSession


@login_required
def submission_list_view(request):
    """List all exam submissions for the current user"""
    submissions = ExamSession.objects.filter(
        user=request.user
    ).select_related('exam').order_by('-created_at')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        submissions = submissions.filter(
            Q(exam__title__icontains=search_query) |
            Q(exam__hsk_level__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(submissions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'submissions/submission_list.html', context)


@login_required
def submission_detail_view(request, submission_id):
    """View detailed results of a specific exam submission"""
    submission = get_object_or_404(
        ExamSession, 
        id=submission_id, 
        user=request.user
    )
      # Get all answers for this submission
    answers = ExamAnswer.objects.filter(
        exam_session=submission
    ).select_related('question', 'selected_choice').order_by('question__id')
    
    # Calculate detailed statistics
    total_questions = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    wrong_answers = total_questions - correct_answers
    accuracy_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Group answers by question type if available
    answer_stats = {}
    for answer in answers:
        question_type = getattr(answer.question, 'question_type', 'general')
        if question_type not in answer_stats:
            answer_stats[question_type] = {'correct': 0, 'total': 0}
        answer_stats[question_type]['total'] += 1
        if answer.is_correct:
            answer_stats[question_type]['correct'] += 1
    
    context = {
        'submission': submission,
        'answers': answers,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'wrong_answers': wrong_answers,
        'accuracy_percentage': round(accuracy_percentage, 1),
        'answer_stats': answer_stats,
    }
    return render(request, 'submissions/submission_detail.html', context)

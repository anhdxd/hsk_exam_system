from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Question, QuestionBank


def question_list_view(request):
    """List all questions"""
    questions = Question.objects.filter(is_active=True)
    context = {
        'questions': questions,
    }
    return render(request, 'questions/question_list.html', context)


def question_detail_view(request, question_id):
    """Question detail view"""
    question = get_object_or_404(Question, id=question_id)
    context = {
        'question': question,
    }
    return render(request, 'questions/question_detail.html', context)


@login_required
def question_create_view(request):
    """Create new question"""
    context = {}
    return render(request, 'questions/question_form.html', context)


@login_required
def import_questions_view(request):
    """Import questions from CSV/JSON"""
    context = {}
    return render(request, 'questions/import_questions.html', context)

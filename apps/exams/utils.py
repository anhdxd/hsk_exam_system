"""
Utility functions for exam management
"""
import random
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from .models import Exam, ExamSession
from apps.questions.models import Question, QuestionType


def generate_random_questions(question_bank, total_questions, hsk_level=None, question_types=None):
    """
    Generate a random selection of questions for an exam
    
    Args:
        question_bank: QuestionBank instance
        total_questions: Number of questions to select
        hsk_level: HSKLevel instance (optional, will use question_bank's level if not provided)
        question_types: List of QuestionType instances to include (optional)
    
    Returns:
        List of Question IDs
    """
    # Build query
    queryset = question_bank.questions.filter(is_active=True)
    
    if hsk_level:
        queryset = queryset.filter(hsk_level=hsk_level)
    else:
        queryset = queryset.filter(hsk_level=question_bank.hsk_level)
    
    if question_types:
        queryset = queryset.filter(question_type__in=question_types)
    
    # Get available questions
    questions = list(queryset.values_list('id', flat=True))
    
    # Shuffle and limit
    random.shuffle(questions)
    return questions[:total_questions]


def distribute_questions_by_type(question_bank, total_questions, hsk_level=None, distribution=None):
    """
    Distribute questions by type for balanced exam
    
    Args:
        question_bank: QuestionBank instance
        total_questions: Total number of questions
        hsk_level: HSKLevel instance
        distribution: Dict mapping QuestionType to number/percentage
                     e.g., {'Đọc hiểu': 0.4, 'Nghe hiểu': 0.3, 'Từ vựng': 0.3}
    
    Returns:
        List of Question IDs
    """
    if not distribution:
        # Default equal distribution among available types
        available_types = QuestionType.objects.filter(
            questions__question_banks=question_bank,
            questions__is_active=True
        ).distinct()
        
        distribution = {qtype: 1.0/len(available_types) for qtype in available_types}
    
    selected_questions = []
    
    for question_type, ratio in distribution.items():
        count = int(total_questions * ratio)
        
        # Get questions of this type
        questions = question_bank.questions.filter(
            is_active=True,
            question_type=question_type,
            hsk_level=hsk_level or question_bank.hsk_level
        ).values_list('id', flat=True)
        
        questions = list(questions)
        random.shuffle(questions)
        selected_questions.extend(questions[:count])
    
    # Fill remaining slots if needed
    remaining = total_questions - len(selected_questions)
    if remaining > 0:
        # Get any remaining questions not already selected
        excluded_ids = selected_questions
        remaining_questions = question_bank.questions.filter(
            is_active=True,
            hsk_level=hsk_level or question_bank.hsk_level
        ).exclude(id__in=excluded_ids).values_list('id', flat=True)
        
        remaining_questions = list(remaining_questions)
        random.shuffle(remaining_questions)
        selected_questions.extend(remaining_questions[:remaining])
    
    # Final shuffle
    random.shuffle(selected_questions)
    return selected_questions[:total_questions]


def check_exam_time_conflicts(exam):
    """
    Check if exam time conflicts with other active exams
    
    Args:
        exam: Exam instance
    
    Returns:
        List of conflicting exams
    """
    conflicts = Exam.objects.filter(
        is_active=True,
        hsk_level=exam.hsk_level
    ).exclude(pk=exam.pk)
    
    if exam.start_date and exam.end_date:
        conflicts = conflicts.filter(
            Q(start_date__range=(exam.start_date, exam.end_date)) |
            Q(end_date__range=(exam.start_date, exam.end_date)) |
            Q(start_date__lte=exam.start_date, end_date__gte=exam.end_date)
        )
    
    return list(conflicts)


def get_exam_statistics(exam):
    """
    Get comprehensive statistics for an exam
    
    Args:
        exam: Exam instance
    
    Returns:
        Dictionary with statistics
    """
    sessions = exam.examsession_set.all()
    completed_sessions = sessions.filter(status='completed')
    
    stats = {
        'total_sessions': sessions.count(),
        'completed_sessions': completed_sessions.count(),
        'in_progress_sessions': sessions.filter(status='in_progress').count(),
        'expired_sessions': sessions.filter(status='expired').count(),
        'not_started_sessions': sessions.filter(status='not_started').count(),
    }
    
    if completed_sessions.exists():
        scores = completed_sessions.values_list('percentage', flat=True)
        stats.update({
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'pass_rate': (completed_sessions.filter(passed=True).count() / len(scores)) * 100,
            'median_score': sorted(scores)[len(scores)//2] if scores else 0,
        })
        
        # Score distribution
        stats['score_distribution'] = {
            '90-100': completed_sessions.filter(percentage__gte=90).count(),
            '80-89': completed_sessions.filter(percentage__gte=80, percentage__lt=90).count(),
            '70-79': completed_sessions.filter(percentage__gte=70, percentage__lt=80).count(),
            '60-69': completed_sessions.filter(percentage__gte=60, percentage__lt=70).count(),
            '0-59': completed_sessions.filter(percentage__lt=60).count(),
        }
    else:
        stats.update({
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'pass_rate': 0,
            'median_score': 0,
            'score_distribution': {
                '90-100': 0, '80-89': 0, '70-79': 0, '60-69': 0, '0-59': 0
            }
        })
    
    return stats


def calculate_estimated_duration(question_count, difficulty_weights=None):
    """
    Calculate estimated exam duration based on question count and difficulty
    
    Args:
        question_count: Number of questions
        difficulty_weights: Dict with time per question by difficulty
                          Default: {'easy': 1.5, 'medium': 2.0, 'hard': 3.0} minutes
    
    Returns:
        Estimated duration in minutes
    """
    if not difficulty_weights:
        difficulty_weights = {
            'easy': 1.5,      # 1.5 minutes per easy question
            'medium': 2.0,    # 2 minutes per medium question
            'hard': 3.0       # 3 minutes per hard question
        }
    
    # Default to medium difficulty if no breakdown provided
    avg_time_per_question = difficulty_weights.get('medium', 2.0)
    
    # Add buffer time (20% extra)
    base_time = question_count * avg_time_per_question
    buffer_time = base_time * 0.2
    
    return int(base_time + buffer_time)


def auto_expire_sessions():
    """
    Automatically expire sessions that have exceeded their time limit
    
    Returns:
        Number of sessions expired
    """
    now = timezone.now()
    expired_count = 0
    
    # Find sessions that should be expired
    active_sessions = ExamSession.objects.filter(
        status='in_progress',
        started_at__isnull=False
    ).select_related('exam')
    
    for session in active_sessions:
        if session.is_expired():
            session.expire_session()
            expired_count += 1
    
    return expired_count


def cleanup_old_sessions(days_old=30):
    """
    Clean up old completed/expired exam sessions
    
    Args:
        days_old: Number of days after which to delete sessions
    
    Returns:
        Number of sessions deleted
    """
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    old_sessions = ExamSession.objects.filter(
        status__in=['completed', 'expired'],
        completed_at__lt=cutoff_date
    )
    
    count = old_sessions.count()
    old_sessions.delete()
    
    return count


def validate_exam_configuration(exam):
    """
    Validate exam configuration and return any issues
    
    Args:
        exam: Exam instance
    
    Returns:
        List of validation errors/warnings
    """
    issues = []
    
    # Check if question bank has enough questions
    available_questions = exam.get_available_questions().count()
    if available_questions < exam.total_questions:
        issues.append(
            f"Ngân hàng câu hỏi chỉ có {available_questions} câu hỏi khả dụng, "
            f"nhưng kỳ thi yêu cầu {exam.total_questions} câu hỏi."
        )
    
    # Check duration reasonableness
    estimated_duration = calculate_estimated_duration(exam.total_questions)
    if exam.duration_minutes < estimated_duration * 0.5:
        issues.append(
            f"Thời gian thi ({exam.duration_minutes} phút) có thể quá ngắn. "
            f"Thời gian đề xuất: {estimated_duration} phút."
        )
    elif exam.duration_minutes > estimated_duration * 3:
        issues.append(
            f"Thời gian thi ({exam.duration_minutes} phút) có thể quá dài. "
            f"Thời gian đề xuất: {estimated_duration} phút."
        )
    
    # Check date validity
    if exam.start_date and exam.end_date:
        if exam.end_date <= exam.start_date:
            issues.append("Ngày kết thúc phải sau ngày bắt đầu.")
        
        # Check if exam duration is longer than available time window
        available_window = (exam.end_date - exam.start_date).total_seconds() / 60
        if exam.duration_minutes > available_window:
            issues.append(
                f"Thời gian thi ({exam.duration_minutes} phút) dài hơn "
                f"khoảng thời gian mở thi ({available_window:.0f} phút)."
            )
    
    # Check for conflicts
    conflicts = check_exam_time_conflicts(exam)
    if conflicts:
        conflict_titles = [c.title for c in conflicts]
        issues.append(
            f"Kỳ thi trùng thời gian với: {', '.join(conflict_titles)}"
        )
    
    return issues


def generate_exam_report(exam):
    """
    Generate comprehensive exam report
    
    Args:
        exam: Exam instance
    
    Returns:
        Dictionary with report data
    """
    stats = get_exam_statistics(exam)
    issues = validate_exam_configuration(exam)
    
    report = {
        'exam': exam,
        'statistics': stats,
        'validation_issues': issues,
        'question_breakdown': {},
        'performance_analysis': {},
    }
    
    # Question breakdown by type
    questions = exam.get_available_questions()
    for qtype in questions.values_list('question_type__name', flat=True).distinct():
        count = questions.filter(question_type__name=qtype).count()
        report['question_breakdown'][qtype] = count
    
    # Performance analysis by question type
    if exam.examsession_set.filter(status='completed').exists():
        completed_sessions = exam.examsession_set.filter(status='completed')
        
        for session in completed_sessions:
            questions_data = session.get_questions_with_answers()
            
            for q_data in questions_data:
                qtype = q_data['question'].question_type.name
                
                if qtype not in report['performance_analysis']:
                    report['performance_analysis'][qtype] = {
                        'total': 0,
                        'correct': 0,
                        'accuracy': 0
                    }
                
                report['performance_analysis'][qtype]['total'] += 1
                if q_data['is_correct']:
                    report['performance_analysis'][qtype]['correct'] += 1
        
        # Calculate accuracy rates
        for qtype, data in report['performance_analysis'].items():
            if data['total'] > 0:
                data['accuracy'] = (data['correct'] / data['total']) * 100
    
    return report

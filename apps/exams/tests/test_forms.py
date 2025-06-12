from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.exams.models import Exam, ExamSession
from apps.exams.forms import ExamForm, StartExamForm, ExamAnswerForm, ExamSearchForm
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank, Question, Choice, QuestionType


User = get_user_model()


class ExamFormTest(TestCase):
    """Test cases for ExamForm"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Basic level"
        )

        self.question_bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level,
            description="Test question bank"
        )

        # Create test questions
        question_type = QuestionType.objects.create(
            name="Multiple Choice",
            description="Multiple choice questions"
        )

        for i in range(10):
            Question.objects.create(
                question_text=f"Question {i+1}",
                question_type=question_type,
                hsk_level=self.hsk_level,
                difficulty='medium',
                points=1,
                is_active=True
            )

        # Add questions to bank
        questions = Question.objects.filter(hsk_level=self.hsk_level)
        self.question_bank.questions.set(questions)

    def test_exam_form_valid_data(self):
        """Test ExamForm with valid data"""
        form_data = {
            'title': 'Test Exam',
            'description': 'Test description',
            'hsk_level': self.hsk_level.id,
            'question_bank': self.question_bank.id,
            'duration_minutes': 60,
            'total_questions': 5,
            'passing_score': 60.0,
            'start_date': timezone.now(),
            'is_active': True,
            'randomize_questions': True,
            'show_results_immediately': True,
            'allow_retake': True,
            'max_attempts': 3,
            'allow_navigation': True,
            'require_full_completion': False
        }

        form = ExamForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_form_invalid_date_range(self):
        """Test ExamForm with invalid date range"""
        form_data = {
            'title': 'Test Exam',
            'description': 'Test description',
            'hsk_level': self.hsk_level.id,
            'question_bank': self.question_bank.id,
            'duration_minutes': 60,
            'total_questions': 5,
            'passing_score': 60.0,
            'start_date': timezone.now(),
            'end_date': timezone.now() - timedelta(days=1),  # End before start
            'is_active': True,
            'randomize_questions': True,
            'show_results_immediately': True,
            'allow_retake': True,
            'max_attempts': 3,
            'allow_navigation': True,
            'require_full_completion': False
        }

        form = ExamForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_exam_form_mismatched_hsk_level(self):
        """Test ExamForm with mismatched HSK level and question bank"""
        # Create different HSK level
        different_hsk = HSKLevel.objects.create(
            level=2,
            name="HSK 2",
            description="Intermediate level"
        )

        form_data = {
            'title': 'Test Exam',
            'description': 'Test description',
            'hsk_level': different_hsk.id,  # Different from question bank
            'question_bank': self.question_bank.id,
            'duration_minutes': 60,
            'total_questions': 5,
            'passing_score': 60.0,
            'start_date': timezone.now(),
            'is_active': True,
            'randomize_questions': True,
            'show_results_immediately': True,
            'allow_retake': True,
            'max_attempts': 3,
            'allow_navigation': True,
            'require_full_completion': False
        }

        form = ExamForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('question_bank', form.errors)

    def test_exam_form_too_many_questions(self):
        """Test ExamForm requesting more questions than available"""
        form_data = {
            'title': 'Test Exam',
            'description': 'Test description',
            'hsk_level': self.hsk_level.id,
            'question_bank': self.question_bank.id,
            'duration_minutes': 60,
            'total_questions': 20,  # More than available (10)
            'passing_score': 60.0,
            'start_date': timezone.now(),
            'is_active': True,
            'randomize_questions': True,
            'show_results_immediately': True,
            'allow_retake': True,
            'max_attempts': 3,
            'allow_navigation': True,
            'require_full_completion': False
        }

        form = ExamForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('total_questions', form.errors)

    def test_exam_form_required_fields(self):
        """Test ExamForm with missing required fields"""
        form_data = {}
        form = ExamForm(data=form_data)
        self.assertFalse(form.is_valid())

        required_fields = ['title', 'hsk_level', 'question_bank',
                           'duration_minutes', 'total_questions', 'passing_score']
        for field in required_fields:
            self.assertIn(field, form.errors)

    def test_exam_form_init_with_instance(self):
        """Test ExamForm initialization with existing instance"""
        exam = Exam.objects.create(
            title="Test Exam",
            description="Test description",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=5,
            passing_score=60.0
        )

        form = ExamForm(instance=exam)
        # Should filter question banks by HSK level
        self.assertEqual(
            list(form.fields['question_bank'].queryset),
            list(QuestionBank.objects.filter(
                hsk_level=self.hsk_level, is_active=True))
        )


class StartExamFormTest(TestCase):
    """Test cases for StartExamForm"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Basic level"
        )

        self.question_bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level,
            description="Test question bank"
        )

        self.exam = Exam.objects.create(
            title="Test Exam",
            description="Test exam description",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=5,
            passing_score=60.0
        )

    def test_start_exam_form_valid(self):
        """Test StartExamForm with valid data"""
        form_data = {'confirm': True}
        form = StartExamForm(self.exam, self.user, data=form_data)
        self.assertTrue(form.is_valid())

    def test_start_exam_form_invalid_confirm(self):
        """Test StartExamForm without confirmation"""
        form_data = {'confirm': False}
        form = StartExamForm(self.exam, self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)

    def test_start_exam_form_with_active_session(self):
        """Test StartExamForm with existing active session"""
        # Create active session
        ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='in_progress',
            started_at=timezone.now()
        )
        form_data = {'confirm': True}
        form = StartExamForm(self.exam, self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_start_exam_form_max_attempts_exceeded(self):
        """Test StartExamForm when max attempts exceeded"""
        # Create max attempts sessions with different timestamps
        for i in range(self.exam.max_attempts):
            session = ExamSession.objects.create(
                exam=self.exam,
                user=self.user,
                status='completed'
            )
            # Modify created_at to avoid uniqueness issues
            session.created_at = timezone.now() - timedelta(minutes=i)
            session.save()

        form_data = {'confirm': True}
        form = StartExamForm(self.exam, self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_start_exam_form_inactive_exam(self):
        """Test StartExamForm with inactive exam"""
        self.exam.is_active = False
        self.exam.save()

        form_data = {'confirm': True}
        form = StartExamForm(self.exam, self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class ExamAnswerFormTest(TestCase):
    """Test cases for ExamAnswerForm"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Basic level"
        )

        self.question_type = QuestionType.objects.create(
            name="Multiple Choice",
            description="Multiple choice questions"
        )

        self.question = Question.objects.create(
            question_text="Test Question",
            question_type=self.question_type,
            hsk_level=self.hsk_level,
            difficulty='medium',
            points=1
        )

        # Create choices
        self.choices = []
        for i in range(4):
            choice = Choice.objects.create(
                question=self.question,
                choice_text=f"Choice {i+1}",
                is_correct=(i == 0),
                order=i
            )
            self.choices.append(choice)

    def test_exam_answer_form_valid(self):
        """Test ExamAnswerForm with valid choice"""
        form_data = {'choice': self.choices[0].id}
        form = ExamAnswerForm(self.question, data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_answer_form_no_choice(self):
        """Test ExamAnswerForm with no choice selected"""
        form_data = {}
        form = ExamAnswerForm(self.question, data=form_data)
        self.assertTrue(form.is_valid())  # Choice is not required

    def test_exam_answer_form_invalid_choice(self):
        """Test ExamAnswerForm with invalid choice"""
        form_data = {'choice': 9999}  # Non-existent choice
        form = ExamAnswerForm(self.question, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('choice', form.errors)

    def test_exam_answer_form_queryset(self):
        """Test ExamAnswerForm choice queryset"""
        form = ExamAnswerForm(self.question)
        # Should only include choices for this question, ordered by order
        expected_choices = list(self.question.choices.all().order_by('order'))
        actual_choices = list(form.fields['choice'].queryset)
        self.assertEqual(actual_choices, expected_choices)


class ExamSearchFormTest(TestCase):
    """Test cases for ExamSearchForm"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Basic level"
        )

    def test_exam_search_form_valid(self):
        """Test ExamSearchForm with valid data"""
        form_data = {
            'search': 'test',
            'hsk_level': self.hsk_level.id,
            'status': 'available'
        }
        form = ExamSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_search_form_empty(self):
        """Test ExamSearchForm with empty data"""
        form_data = {}
        form = ExamSearchForm(data=form_data)
        self.assertTrue(form.is_valid())  # All fields are optional

    def test_exam_search_form_partial_data(self):
        """Test ExamSearchForm with partial data"""
        form_data = {'search': 'test exam'}
        form = ExamSearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_exam_search_form_invalid_hsk_level(self):
        """Test ExamSearchForm with invalid HSK level"""
        form_data = {'hsk_level': 9999}  # Non-existent HSK level
        form = ExamSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('hsk_level', form.errors)

    def test_exam_search_form_invalid_status(self):
        """Test ExamSearchForm with invalid status"""
        form_data = {'status': 'invalid_status'}
        form = ExamSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_exam_search_form_queryset(self):
        """Test ExamSearchForm HSK level queryset"""
        # Create additional HSK level
        hsk_level_2 = HSKLevel.objects.create(
            level=2,
            name="HSK 2",
            description="Intermediate level"
        )

        form = ExamSearchForm()
        # Should include all HSK levels ordered by level
        expected_levels = list(HSKLevel.objects.all().order_by('level'))
        actual_levels = list(form.fields['hsk_level'].queryset)
        self.assertEqual(actual_levels, expected_levels)

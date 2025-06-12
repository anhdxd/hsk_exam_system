from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.exams.models import Exam, ExamSession
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank, Question, Choice, QuestionType


User = get_user_model()


class ExamModelTest(TestCase):
    """Test cases for Exam model"""

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
        
        self.exam = Exam.objects.create(
            title="Test Exam",
            description="Test exam description",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=20,
            passing_score=60.0
        )

    def test_exam_creation(self):
        """Test exam creation with valid data"""
        self.assertEqual(self.exam.title, "Test Exam")
        self.assertEqual(self.exam.hsk_level, self.hsk_level)
        self.assertEqual(self.exam.duration_minutes, 60)
        self.assertTrue(self.exam.is_active)

    def test_exam_str(self):
        """Test exam string representation"""
        expected = f"Test Exam (HSK {self.hsk_level.level})"
        self.assertEqual(str(self.exam), expected)

    def test_exam_availability(self):
        """Test exam availability checking"""
        # Test active exam
        self.assertTrue(self.exam.is_available())
        
        # Test inactive exam
        self.exam.is_active = False
        self.exam.save()
        self.assertFalse(self.exam.is_available())
        
        # Test exam with future start date
        self.exam.is_active = True
        self.exam.start_date = timezone.now() + timedelta(days=1)
        self.exam.save()
        self.assertFalse(self.exam.is_available())
        
        # Test exam with past end date
        self.exam.start_date = timezone.now() - timedelta(days=2)
        self.exam.end_date = timezone.now() - timedelta(days=1)
        self.exam.save()
        self.assertFalse(self.exam.is_available())

    def test_duration_display(self):
        """Test duration display formatting"""
        # Test minutes only
        self.exam.duration_minutes = 45
        self.assertEqual(self.exam.get_duration_display(), "45m")
        
        # Test hours and minutes
        self.exam.duration_minutes = 90
        self.assertEqual(self.exam.get_duration_display(), "1h 30m")
        
        # Test hours only
        self.exam.duration_minutes = 120
        self.assertEqual(self.exam.get_duration_display(), "2h")

    def test_generate_question_order(self):
        """Test question order generation"""
        # Create test questions
        question_type = QuestionType.objects.create(
            name="Multiple Choice",
            description="Multiple choice questions"
        )
        
        for i in range(5):
            Question.objects.create(
                question_text=f"Question {i+1}",
                question_type=question_type,
                hsk_level=self.hsk_level,
                difficulty='medium',
                points=1
            )
        
        # Add questions to bank
        questions = Question.objects.filter(hsk_level=self.hsk_level)
        self.question_bank.questions.set(questions)
        
        # Test question order generation
        question_order = self.exam.generate_question_order()
        self.assertLessEqual(len(question_order), self.exam.total_questions)
        self.assertLessEqual(len(question_order), questions.count())

    def test_can_user_take_exam(self):
        """Test user exam eligibility checking"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Test user can take exam
        can_take, message = self.exam.can_user_take_exam(user)
        self.assertTrue(can_take)
        self.assertEqual(message, "OK")
        
        # Test with active session
        session = ExamSession.objects.create(
            exam=self.exam,
            user=user,
            status='in_progress',
            started_at=timezone.now()
        )
        
        can_take, message = self.exam.can_user_take_exam(user)
        self.assertFalse(can_take)
        self.assertIn("đang có phiên thi", message)
        
        # Test attempt limit
        session.status = 'completed'
        session.save()
        
        # Create max attempts
        for i in range(self.exam.max_attempts - 1):
            ExamSession.objects.create(
                exam=self.exam,
                user=user,
                status='completed'
            )
        
        can_take, message = self.exam.can_user_take_exam(user)
        self.assertFalse(can_take)
        self.assertIn("vượt quá số lần thi", message)


class ExamSessionModelTest(TestCase):
    """Test cases for ExamSession model"""

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
        
        self.session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )

    def test_session_creation(self):
        """Test exam session creation"""
        self.assertEqual(self.session.exam, self.exam)
        self.assertEqual(self.session.user, self.user)
        self.assertEqual(self.session.status, 'not_started')
        self.assertIsNone(self.session.started_at)

    def test_session_str(self):
        """Test session string representation"""
        expected = f"{self.user.username} - {self.exam.title} (Chưa bắt đầu)"
        self.assertEqual(str(self.session), expected)

    def test_start_session(self):
        """Test starting exam session"""
        # Test successful start
        result = self.session.start_session()
        self.assertTrue(result)
        self.assertEqual(self.session.status, 'in_progress')
        self.assertIsNotNone(self.session.started_at)
        self.assertEqual(self.session.time_remaining, self.exam.duration_minutes)
        
        # Test can't start already started session
        result = self.session.start_session()
        self.assertFalse(result)

    def test_complete_session(self):
        """Test completing exam session"""
        # Start session first
        self.session.start_session()
        
        # Test successful completion
        result = self.session.complete_session()
        self.assertTrue(result)
        self.assertEqual(self.session.status, 'completed')
        self.assertIsNotNone(self.session.completed_at)
        
        # Test can't complete already completed session
        result = self.session.complete_session()
        self.assertFalse(result)

    def test_expire_session(self):
        """Test expiring exam session"""
        self.session.start_session()
        
        result = self.session.expire_session()
        self.assertTrue(result)
        self.assertEqual(self.session.status, 'expired')
        self.assertIsNotNone(self.session.completed_at)

    def test_is_expired(self):
        """Test session expiration checking"""
        # Not started session
        self.assertFalse(self.session.is_expired())
        
        # Started but not expired
        self.session.start_session()
        self.assertFalse(self.session.is_expired())
        
        # Expired session
        self.session.started_at = timezone.now() - timedelta(
            minutes=self.exam.duration_minutes + 1
        )
        self.session.save()
        self.assertTrue(self.session.is_expired())

    def test_time_remaining(self):
        """Test time remaining calculation"""
        self.session.start_session()
        
        # Should have positive time remaining
        remaining = self.session.get_time_remaining_seconds()
        self.assertGreater(remaining, 0)
        
        # Test expired session
        self.session.started_at = timezone.now() - timedelta(hours=2)
        self.session.save()
        remaining = self.session.get_time_remaining_seconds()
        self.assertEqual(remaining, 0)

    def test_navigation_methods(self):
        """Test question navigation methods"""
        # Set up questions order
        self.session.questions_order = [1, 2, 3, 4, 5]
        self.session.current_question_index = 2
        self.session.save()
        
        # Test has_next_question
        self.assertTrue(self.session.has_next_question())
        
        # Test has_previous_question
        self.assertTrue(self.session.has_previous_question())
        
        # Test at beginning
        self.session.current_question_index = 0
        self.session.save()
        self.assertFalse(self.session.has_previous_question())
        
        # Test at end
        self.session.current_question_index = 4
        self.session.save()
        self.assertFalse(self.session.has_next_question())

    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        self.session.questions_order = [1, 2, 3, 4, 5]
        
        # Test at beginning
        self.session.current_question_index = 0
        progress = self.session.get_progress_percentage()
        self.assertEqual(progress, 0)
        
        # Test at middle
        self.session.current_question_index = 2
        progress = self.session.get_progress_percentage()
        self.assertEqual(progress, 40)
        
        # Test at end
        self.session.current_question_index = 4
        progress = self.session.get_progress_percentage()
        self.assertEqual(progress, 80)

    def test_save_and_get_answer(self):
        """Test saving and retrieving answers"""
        # Save answer
        self.session.save_answer(1, 2)
        
        # Retrieve answer
        answer = self.session.get_answer(1)
        self.assertEqual(answer, 2)
        
        # Test non-existent answer
        answer = self.session.get_answer(999)
        self.assertIsNone(answer)

    def test_calculate_results(self):
        """Test results calculation"""
        # Create test questions and choices
        question_type = QuestionType.objects.create(
            name="Multiple Choice",
            description="Multiple choice questions"
        )
        
        questions = []
        for i in range(3):
            question = Question.objects.create(
                question_text=f"Question {i+1}",
                question_type=question_type,
                hsk_level=self.hsk_level,
                difficulty='medium',
                points=10
            )
            
            # Create choices
            for j in range(4):
                Choice.objects.create(
                    question=question,
                    choice_text=f"Choice {j+1}",
                    is_correct=(j == 0),  # First choice is correct
                    order=j
                )
            
            questions.append(question)
        
        # Set up session with questions
        self.session.questions_order = [q.id for q in questions]
          # Save answers (1 correct, 2 incorrect)
        correct_choice_1 = questions[0].choices.filter(is_correct=True).first()
        incorrect_choice_1 = questions[1].choices.filter(is_correct=False).first()
        incorrect_choice_2 = questions[2].choices.filter(is_correct=False).first()
        
        self.session.save_answer(questions[0].id, correct_choice_1.id)
        self.session.save_answer(questions[1].id, incorrect_choice_1.id)
        self.session.save_answer(questions[2].id, incorrect_choice_2.id)
        
        # Calculate results
        self.session.calculate_results()
        
        # Check results
        self.assertEqual(self.session.total_points, 30)  # 3 questions * 10 points
        self.assertEqual(self.session.earned_points, 10)  # 1 correct * 10 points
        self.assertEqual(self.session.percentage, (10/30) * 100)  # 33.33%
        self.assertFalse(self.session.passed)  # Below 60% passing score

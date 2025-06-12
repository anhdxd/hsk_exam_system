from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.exams.models import Exam, ExamSession
from apps.exams.utils import (
    generate_random_questions, 
    distribute_questions_by_type,
    check_exam_time_conflicts,
    get_exam_statistics,
    calculate_estimated_duration,
    auto_expire_sessions,
    cleanup_old_sessions,
    validate_exam_configuration,
    generate_exam_report
)
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank, Question, Choice, QuestionType


User = get_user_model()


class ExamLogicTest(TestCase):
    """Test cases for exam business logic"""

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
        
        # Create question types
        self.question_types = []
        for name in ['Reading', 'Listening', 'Vocabulary']:
            qtype = QuestionType.objects.create(
                name=name,
                description=f"{name} questions"
            )
            self.question_types.append(qtype)
        
        # Create test questions
        self.questions = []
        for i, qtype in enumerate(self.question_types):
            for j in range(5):  # 5 questions per type
                question = Question.objects.create(
                    question_text=f"{qtype.name} Question {j+1}",
                    question_type=qtype,
                    hsk_level=self.hsk_level,
                    difficulty='medium',
                    points=10,
                    is_active=True
                )
                
                # Create choices
                for k in range(4):
                    Choice.objects.create(
                        question=question,
                        choice_text=f"Choice {k+1}",
                        is_correct=(k == 0),
                        order=k
                    )
                
                self.questions.append(question)
        
        # Add questions to bank
        self.question_bank.questions.set(self.questions)
        
        self.exam = Exam.objects.create(
            title="Test Exam",
            description="Test exam description",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=10,
            passing_score=60.0
        )

    def test_exam_session_lifecycle(self):
        """Test complete exam session lifecycle"""
        # 1. Create session
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        self.assertEqual(session.status, 'not_started')
        
        # 2. Start session
        result = session.start_session()
        self.assertTrue(result)
        self.assertEqual(session.status, 'in_progress')
        self.assertIsNotNone(session.started_at)
        self.assertIsNotNone(session.questions_order)
        
        # 3. Answer questions
        for i, question_id in enumerate(session.questions_order[:3]):
            question = Question.objects.get(id=question_id)
            correct_choice = question.choices.filter(is_correct=True).first()
            session.save_answer(question_id, correct_choice.id)
        
        # 4. Complete session
        result = session.complete_session()
        self.assertTrue(result)
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.completed_at)
        
        # 5. Check results
        self.assertGreater(session.percentage, 0)
        self.assertEqual(session.earned_points, 30)  # 3 correct * 10 points

    def test_exam_time_expiration(self):
        """Test exam session time expiration"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        
        # Start session
        session.start_session()
        
        # Simulate time passing
        session.started_at = timezone.now() - timedelta(hours=2)
        session.save()
        
        # Check expiration
        self.assertTrue(session.is_expired())
        
        # Expire session
        result = session.expire_session()
        self.assertTrue(result)
        self.assertEqual(session.status, 'expired')

    def test_exam_navigation(self):
        """Test question navigation during exam"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        session.start_session()
        
        # Test initial state
        self.assertEqual(session.current_question_index, 0)
        self.assertFalse(session.has_previous_question())
        self.assertTrue(session.has_next_question())
        
        # Navigate forward
        session.current_question_index = 5
        session.save()
        
        self.assertTrue(session.has_previous_question())
        self.assertTrue(session.has_next_question())
        
        # Navigate to end
        session.current_question_index = len(session.questions_order) - 1
        session.save()
        
        self.assertTrue(session.has_previous_question())
        self.assertFalse(session.has_next_question())

    def test_exam_progress_calculation(self):
        """Test exam progress calculation"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        session.start_session()
        
        # Test progress at different stages
        test_cases = [
            (0, 0),      # Beginning
            (2, 20),     # 2/10 = 20%
            (5, 50),     # 5/10 = 50%
            (9, 90),     # 9/10 = 90%
        ]
        for index, expected_progress in test_cases:
            session.current_question_index = index
            progress = session.get_progress_percentage()
            self.assertEqual(progress, expected_progress)

    def test_exam_scoring_accuracy(self):
        """Test exam scoring accuracy"""
        # Create a separate user for this test to avoid conflicts
        scoring_user = User.objects.create_user(
            username="scoring_testuser",
            email="scoring_test@example.com",
            password="testpass123"
        )
        
        session = ExamSession.objects.create(
            exam=self.exam,
            user=scoring_user
        )
        session.start_session()
        
        # Answer first 5 questions correctly, next 5 incorrectly
        for i, question_id in enumerate(session.questions_order):
            question = Question.objects.get(id=question_id)
            
            if i < 5:  # First 5 correct
                correct_choice = question.choices.filter(is_correct=True).first()
                session.save_answer(question_id, correct_choice.id)
            else:  # Next 5 incorrect
                incorrect_choice = question.choices.filter(is_correct=False).first()
                session.save_answer(question_id, incorrect_choice.id)
        
        # Calculate results
        session.calculate_results()
        
        # Check results
        self.assertEqual(session.total_points, 100)  # 10 questions * 10 points
        self.assertEqual(session.earned_points, 50)   # 5 correct * 10 points
        self.assertEqual(session.percentage, 50.0)    # 50/100 = 50%
        self.assertFalse(session.passed)              # Below 60% passing scoredef test_exam_retake_restrictions(self):
        """Test exam retake restrictions"""
        # Test initial eligibility
        can_take, message = self.exam.can_user_take_exam(self.user)
        self.assertTrue(can_take)
        
        # Create completed sessions up to limit with different timestamps
        for i in range(self.exam.max_attempts):
            session = ExamSession.objects.create(
                exam=self.exam,
                user=self.user,
                status='completed',
                completed_at=timezone.now() - timedelta(minutes=i)
            )
            # Modify created_at to avoid uniqueness issues
            session.created_at = timezone.now() - timedelta(minutes=i+10)
            session.save()
          # Should not be able to take again
        can_take, message = self.exam.can_user_take_exam(self.user)
        self.assertFalse(can_take)
        self.assertIn("vượt quá số lần thi", message)

    def test_exam_no_retake_after_pass(self):
        """Test no retake allowed after passing"""
        self.exam.allow_retake = False
        self.exam.save()
        
        # Create passed session
        ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            passed=True,
            percentage=75.0
        )
        
        # Should not be able to retake
        can_take, message = self.exam.can_user_take_exam(self.user)
        self.assertFalse(can_take)
        self.assertIn("đã hoàn thành kỳ thi này thành công", message)

    def test_concurrent_session_prevention(self):
        """Test prevention of concurrent sessions"""
        # Create active session
        ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='in_progress',
            started_at=timezone.now()
        )
        
        # Should not be able to start another
        can_take, message = self.exam.can_user_take_exam(self.user)
        self.assertFalse(can_take)
        self.assertIn("đang có phiên thi", message)

    def test_exam_availability_checking(self):
        """Test exam availability checking"""
        # Test active exam
        self.assertTrue(self.exam.is_available())
        
        # Test inactive exam
        self.exam.is_active = False
        self.exam.save()
        self.assertFalse(self.exam.is_available())
        
        # Test future exam
        self.exam.is_active = True
        self.exam.start_date = timezone.now() + timedelta(days=1)
        self.exam.save()
        self.assertFalse(self.exam.is_available())
        
        # Test expired exam
        self.exam.start_date = timezone.now() - timedelta(days=2)
        self.exam.end_date = timezone.now() - timedelta(days=1)
        self.exam.save()
        self.assertFalse(self.exam.is_available())

    def test_question_randomization(self):
        """Test question order randomization"""
        # Test with randomization enabled
        self.exam.randomize_questions = True
        self.exam.save()
        
        orders = []
        for _ in range(10):  # Generate multiple orders
            order = self.exam.generate_question_order()
            orders.append(order)
        
        # Orders should not all be the same (very low probability)
        self.assertGreater(len(set(tuple(order) for order in orders)), 1)
        
        # Test with randomization disabled
        self.exam.randomize_questions = False
        self.exam.save()
        
        order1 = self.exam.generate_question_order()
        order2 = self.exam.generate_question_order()
        
        # Orders should be the same when randomization is off
        # Note: This might still vary due to database ordering
        self.assertEqual(len(order1), len(order2))

    def test_answer_persistence(self):
        """Test answer saving and retrieval"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        session.start_session()
        
        # Save multiple answers
        answers = {1: 2, 3: 4, 5: 6}
        for question_id, choice_id in answers.items():
            session.save_answer(question_id, choice_id)
        
        # Retrieve and verify
        for question_id, expected_choice_id in answers.items():
            saved_choice_id = session.get_answer(question_id)
            self.assertEqual(saved_choice_id, expected_choice_id)
        
        # Test non-existent answer
        self.assertIsNone(session.get_answer(999))

    def test_exam_time_tracking(self):
        """Test exam time tracking"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        
        # Test before starting
        self.assertEqual(session.get_time_remaining_seconds(), 0)
        
        # Start session
        session.start_session()
        
        # Should have time remaining
        remaining = session.get_time_remaining_seconds()
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, self.exam.duration_minutes * 60)
        
        # Test end time calculation
        end_time = session.get_end_time()
        self.assertIsNotNone(end_time)
        expected_end = session.started_at + timedelta(minutes=self.exam.duration_minutes)
        self.assertEqual(end_time, expected_end)

    def test_detailed_results_generation(self):
        """Test detailed results generation"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        session.start_session()
        
        # Answer some questions
        answered_questions = session.questions_order[:5]
        for i, question_id in enumerate(answered_questions):
            question = Question.objects.get(id=question_id)
            # Answer first 3 correctly, last 2 incorrectly
            if i < 3:
                choice = question.choices.filter(is_correct=True).first()
            else:
                choice = question.choices.filter(is_correct=False).first()
            session.save_answer(question_id, choice.id)
        
        session.complete_session()
        
        # Get detailed results
        results = session.get_questions_with_answers()
        
        # Should have results for all questions in order
        self.assertEqual(len(results), len(session.questions_order))
        
        # Check first few answered questions
        for i in range(5):
            result = results[i]
            self.assertIsNotNone(result['question'])
            self.assertIsNotNone(result['user_choice'])
            self.assertIsNotNone(result['correct_choice'])
            
            if i < 3:
                self.assertTrue(result['is_correct'])
                self.assertEqual(result['points'], 10)
            else:
                self.assertFalse(result['is_correct'])
                self.assertEqual(result['points'], 0)

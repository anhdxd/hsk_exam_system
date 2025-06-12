from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.exams.models import Exam, ExamSession, ExamAnswer
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank, Question, Choice, QuestionType


User = get_user_model()


class ExamSubmissionFlowTest(TestCase):
    """Test cases for exam submission flow"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        self.hsk_level = HSKLevel.objects.create(
            level=3,
            name="HSK 3",
            description="Intermediate level"
        )

        self.question_bank = QuestionBank.objects.create(
            name="HSK 3 Bank",
            hsk_level=self.hsk_level,
            description="HSK 3 question bank"
        )
        
        # Create test questions with choices
        question_type = QuestionType.objects.create(
            name="Multiple Choice",
            description="Multiple choice questions"
        )
        
        self.questions = []
        for i in range(3):
            question = Question.objects.create(
                question_text=f"Test question {i+1}",
                question_type=question_type,
                hsk_level=self.hsk_level,
                difficulty='easy',
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
            
            self.questions.append(question)
            self.question_bank.questions.add(question)
        
        self.exam = Exam.objects.create(
            title="HSK 3 Submission Test",
            description="HSK 3 exam for testing submission flow",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=3,
            passing_score=60.0
        )

    def test_complete_submission_flow(self):
        """Test complete submission flow from start to result"""
        self.client.login(username="testuser", password="testpass123")
        
        # 1. Start exam
        response = self.client.post(reverse('exams:start', args=[self.exam.pk]), {
            'confirm': True
        })
        self.assertEqual(response.status_code, 302)
        
        # Get the created session
        session = ExamSession.objects.filter(user=self.user, exam=self.exam).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.status, 'in_progress')
        
        # 2. Answer questions
        for i, question in enumerate(self.questions):
            # Get correct choice
            correct_choice = question.choices.filter(is_correct=True).first()
            
            # Submit answer
            response = self.client.post(reverse('exams:take_exam', args=[session.pk]), {
                'action': 'next',
                'choice': correct_choice.id
            })
            
            if i < len(self.questions) - 1:
                self.assertEqual(response.status_code, 302)
            else:
                # Last question should complete exam
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.endswith(f'/session/{session.pk}/result/'))
        
        # 3. Check session is completed
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertTrue(session.passed)
        self.assertEqual(session.percentage, 100.0)
        
        # 4. Check answers were saved
        answers = ExamAnswer.objects.filter(exam_session=session)
        self.assertEqual(answers.count(), 3)
        self.assertTrue(all(answer.is_correct for answer in answers))

    def test_submission_history_view(self):
        """Test submission history view"""
        self.client.login(username="testuser", password="testpass123")
        
        # Create completed session with answers
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=20,
            total_points=30,
            percentage=66.7,
            passed=True,
            started_at=timezone.now() - timedelta(hours=1),
            completed_at=timezone.now()
        )
        session.questions_order = [q.id for q in self.questions]
        session.save()
        
        # Create some answers
        for question in self.questions[:2]:
            correct_choice = question.choices.filter(is_correct=True).first()
            ExamAnswer.objects.create(
                exam_session=session,
                question=question,
                selected_choice=correct_choice,
                is_correct=True,
                points_earned=10
            )
        
        # Test history view
        response = self.client.get(reverse('exams:submission_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, session.exam.title)
        self.assertContains(response, "66.7%")

    def test_submission_detail_view(self):
        """Test submission detail view"""
        self.client.login(username="testuser", password="testpass123")
        
        # Create completed session
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=20,
            total_points=30,
            percentage=66.7,
            passed=True,
            started_at=timezone.now() - timedelta(hours=1),
            completed_at=timezone.now()
        )
        session.questions_order = [q.id for q in self.questions]
        session.save()
        
        # Create answers
        for i, question in enumerate(self.questions):
            if i < 2:  # First 2 correct
                choice = question.choices.filter(is_correct=True).first()
                is_correct = True
                points = 10
            else:  # Last one incorrect
                choice = question.choices.filter(is_correct=False).first()
                is_correct = False
                points = 0
                
            ExamAnswer.objects.create(
                exam_session=session,
                question=question,
                selected_choice=choice,
                is_correct=is_correct,
                points_earned=points
            )
        
        # Test detail view
        response = self.client.get(reverse('exams:submission_detail', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chi tiết bài làm")
        self.assertContains(response, session.exam.title)
        self.assertContains(response, "66.7%")

    def test_submission_search_and_filter(self):
        """Test submission history search and filter"""
        self.client.login(username="testuser", password="testpass123")
        
        # Create multiple sessions
        passed_session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=25,
            total_points=30,
            percentage=83.3,
            passed=True,
            completed_at=timezone.now()
        )
        
        failed_session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=15,
            total_points=30,
            percentage=50.0,
            passed=False,
            completed_at=timezone.now()
        )
        
        # Test search
        response = self.client.get(reverse('exams:submission_history'), {
            'search': 'HSK 3'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.exam.title)
        
        # Test filter passed
        response = self.client.get(reverse('exams:submission_history'), {
            'result': 'passed'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "83.3%")
        self.assertNotContains(response, "50.0%")
        
        # Test filter failed
        response = self.client.get(reverse('exams:submission_history'), {
            'result': 'failed'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "50.0%")
        self.assertNotContains(response, "83.3%")

    def test_submission_access_control(self):
        """Test access control for submission views"""
        # Create another user
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpass123"
        )
        
        # Create session for other user
        other_session = ExamSession.objects.create(
            exam=self.exam,
            user=other_user,
            status='completed',
            earned_points=20,
            total_points=30,
            percentage=66.7,
            passed=True,
            completed_at=timezone.now()
        )
        
        # Login as first user
        self.client.login(username="testuser", password="testpass123")
        
        # Try to access other user's submission
        response = self.client.get(reverse('exams:submission_detail', args=[other_session.pk]))
        self.assertEqual(response.status_code, 404)

    def test_exam_answer_model_save(self):
        """Test ExamAnswer model save method auto-calculation"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='in_progress'
        )
        
        question = self.questions[0]
        correct_choice = question.choices.filter(is_correct=True).first()
        incorrect_choice = question.choices.filter(is_correct=False).first()
        
        # Test correct answer
        correct_answer = ExamAnswer.objects.create(
            exam_session=session,
            question=question,
            selected_choice=correct_choice
        )
        self.assertTrue(correct_answer.is_correct)
        self.assertEqual(correct_answer.points_earned, question.points)
        
        # Test incorrect answer
        incorrect_answer = ExamAnswer.objects.create(
            exam_session=session,
            question=self.questions[1],
            selected_choice=incorrect_choice
        )
        self.assertFalse(incorrect_answer.is_correct)
        self.assertEqual(incorrect_answer.points_earned, 0.0)

    def test_submission_statistics_calculation(self):
        """Test statistics calculation in submission detail view"""
        self.client.login(username="testuser", password="testpass123")
        
        # Create session with mixed results
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=20,
            total_points=30,
            percentage=66.7,
            passed=True,
            completed_at=timezone.now()
        )
        
        # Create answers with different results
        correct_answers = 0
        for i, question in enumerate(self.questions):
            if i < 2:  # 2 correct
                choice = question.choices.filter(is_correct=True).first()
                is_correct = True
                correct_answers += 1
            else:  # 1 incorrect
                choice = question.choices.filter(is_correct=False).first()
                is_correct = False
                
            ExamAnswer.objects.create(
                exam_session=session,
                question=question,
                selected_choice=choice,
                is_correct=is_correct,
                points_earned=10 if is_correct else 0
            )
        
        # Test detail view contains correct statistics
        response = self.client.get(reverse('exams:submission_detail', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertEqual(response.context['correct_answers'], 2)
        self.assertEqual(response.context['wrong_answers'], 1)
        self.assertEqual(response.context['total_questions'], 3)
        self.assertAlmostEqual(response.context['accuracy_percentage'], 66.7, places=1)

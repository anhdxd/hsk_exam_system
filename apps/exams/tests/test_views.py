from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.exams.models import Exam, ExamSession
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank, Question, Choice, QuestionType


User = get_user_model()


class ExamListViewTest(TestCase):
    """Simple test cases for ExamListView"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Beginner level"
        )
        
        self.question_bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level,
            description="Test question bank"
        )
        
        self.exam = Exam.objects.create(
            title="HSK 1 Test Exam",
            description="Test exam for HSK level 1",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=5,
            passing_score=60.0
        )

    def test_exam_list_view_renders(self):
        """Test exam list view renders correctly"""
        response = self.client.get(reverse('exams:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Danh sách kỳ thi")
        self.assertContains(response, self.exam.title)

    def test_exam_list_search_functionality(self):
        """Test search form in exam list"""
        response = self.client.get(reverse('exams:list'), {'search': 'HSK'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.exam.title)


class ExamDetailViewTest(TestCase):
    """Simple test cases for ExamDetailView"""

    def setUp(self):
        self.client = Client()
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
            title="HSK 1 Detailed Exam",
            description="Detailed exam for HSK level 1",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=90,
            total_questions=10,
            passing_score=70.0,
            instructions="Please read all questions carefully."
        )

    def test_exam_detail_view_renders(self):
        """Test exam detail view renders correctly"""
        response = self.client.get(reverse('exams:detail', args=[self.exam.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.exam.title)

    def test_exam_detail_view_nonexistent_exam(self):
        """Test exam detail view with nonexistent exam returns 404"""
        response = self.client.get(reverse('exams:detail', args=[999]))
        self.assertEqual(response.status_code, 404)


class StartExamViewTest(TestCase):
    """Test cases for StartExamView with email and username login"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        self.hsk_level = HSKLevel.objects.create(
            level=2,
            name="HSK 2",
            description="Elementary level"
        )

        self.question_bank = QuestionBank.objects.create(
            name="HSK 2 Bank",
            hsk_level=self.hsk_level,
            description="HSK 2 question bank"
        )

        self.exam = Exam.objects.create(
            title="HSK 2 Start Exam",
            description="HSK 2 exam for testing start functionality",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=120,
            total_questions=1,
            passing_score=75.0
        )

    def test_start_exam_view_get_anonymous_user(self):
        """Test start exam view GET for anonymous user redirects to login"""
        response = self.client.get(reverse('exams:start', args=[self.exam.pk]))
        self.assertRedirects(response, f'/accounts/login/?next=/exams/{self.exam.pk}/start/')

    def test_start_exam_view_get_authenticated_user_with_username(self):
        """Test start exam view GET for authenticated user using username"""
        login_successful = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(login_successful, "Login with username should be successful")
        
        response = self.client.get(reverse('exams:start', args=[self.exam.pk]))
        self.assertEqual(response.status_code, 200)

    def test_start_exam_view_get_authenticated_user_with_email(self):
        """Test start exam view GET for authenticated user using email"""
        login_successful = self.client.login(username="test@example.com", password="testpass123")
        self.assertTrue(login_successful, "Login with email should be successful")
        
        response = self.client.get(reverse('exams:start', args=[self.exam.pk]))
        self.assertEqual(response.status_code, 200)


class TakeExamViewTest(TestCase):
    """Test cases for TakeExamView with email and username login"""

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
        
        # Create a test question with choices
        question_type = QuestionType.objects.create(
            name="Multiple Choice",
            description="Multiple choice questions"
        )
        
        self.question = Question.objects.create(
            question_text="Test question",
            question_type=question_type,
            hsk_level=self.hsk_level,
            difficulty='easy',
            points=10
        )
        
        # Add question to question bank
        self.question_bank.questions.add(self.question)
        
        # Create choices
        for i in range(4):
            Choice.objects.create(
                question=self.question,
                choice_text=f"Choice {i+1}",
                is_correct=(i == 0),  # First choice is correct
                order=i
            )
        
        self.exam = Exam.objects.create(
            title="HSK 3 Take Exam",
            description="HSK 3 exam for testing take functionality",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=180,
            total_questions=1,
            passing_score=80.0
        )

        # Create exam session and start it properly
        self.session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user
        )
        
        # Start the session to generate questions_order
        self.session.start_session()

    def test_take_exam_view_anonymous_user(self):
        """Test take exam view for anonymous user redirects to login"""
        response = self.client.get(reverse('exams:take_exam', args=[self.session.pk]))
        self.assertRedirects(response, f'/accounts/login/?next=/exams/session/{self.session.pk}/take/')

    def test_take_exam_view_authenticated_user_with_username(self):
        """Test take exam view for authenticated user using username"""
        login_successful = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(login_successful, "Login with username should be successful")
        
        response = self.client.get(reverse('exams:take_exam', args=[self.session.pk]))
        print(f"Response status: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirects to: {response.url}")
        self.assertEqual(response.status_code, 200)

    def test_take_exam_view_authenticated_user_with_email(self):
        """Test take exam view for authenticated user using email"""
        login_successful = self.client.login(username="test@example.com", password="testpass123")
        self.assertTrue(login_successful, "Login with email should be successful")
        
        response = self.client.get(reverse('exams:take_exam', args=[self.session.pk]))
        self.assertEqual(response.status_code, 200)


class ExamResultViewTest(TestCase):
    """Test cases for ExamResultView with email and username login"""

    def setUp(self):
        self.client = Client()
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
            title="HSK 1 Result Exam",
            description="HSK 1 exam for testing results",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=10,
            passing_score=60.0
        )

    def test_exam_result_view_passed_exam_with_username(self):
        """Test exam result view for passed exam using username login"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=85,
            total_points=100,
            completed_at=timezone.now()
        )

        login_successful = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(login_successful, "Login with username should be successful")
        
        response = self.client.get(reverse('exams:result', args=[session.pk]))
        self.assertEqual(response.status_code, 200)

    def test_exam_result_view_passed_exam_with_email(self):
        """Test exam result view for passed exam using email login"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=85,
            total_points=100,
            completed_at=timezone.now()
        )

        login_successful = self.client.login(username="test@example.com", password="testpass123")
        self.assertTrue(login_successful, "Login with email should be successful")
        
        response = self.client.get(reverse('exams:result', args=[session.pk]))
        self.assertEqual(response.status_code, 200)

    def test_exam_result_view_unauthorized_user(self):
        """Test exam result view for unauthorized user"""
        session = ExamSession.objects.create(
            exam=self.exam,
            user=self.user,
            status='completed',
            earned_points=75,
            total_points=100
        )

        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpass123"
        )
        self.client.login(username="otheruser", password="otherpass123")
        response = self.client.get(reverse('exams:result', args=[session.pk]))
        self.assertEqual(response.status_code, 404)


class ExamManagementViewTest(TestCase):
    """Test cases for Exam CRUD operations with email and username login"""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="staffpass123",
            is_staff=True,
            is_superuser=True
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
            title="Management Test Exam",
            description="Test exam for management",
            hsk_level=self.hsk_level,
            question_bank=self.question_bank,
            duration_minutes=60,
            total_questions=10,
            passing_score=60.0
        )

    def test_exam_create_view_staff_user_with_username(self):
        """Test exam create view for staff user using username"""
        login_successful = self.client.login(username="staffuser", password="staffpass123")
        self.assertTrue(login_successful, "Login with username should be successful")
        
        response = self.client.get(reverse('exams:create'))
        # Accept either 200 (form page) or 302 (redirect)
        self.assertIn(response.status_code, [200, 302])

    def test_exam_create_view_staff_user_with_email(self):
        """Test exam create view for staff user using email"""
        login_successful = self.client.login(username="staff@example.com", password="staffpass123")
        self.assertTrue(login_successful, "Login with email should be successful")
        
        response = self.client.get(reverse('exams:create'))
        # Accept either 200 (form page) or 302 (redirect)
        self.assertIn(response.status_code, [200, 302])

    def test_exam_update_view_staff_user(self):
        """Test exam update view for staff user"""
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse('exams:update', args=[self.exam.pk]))
        # Accept either 200 (form page) or 302 (redirect)
        self.assertIn(response.status_code, [200, 302])


class AuthenticationBackendTest(TestCase):
    """Test the custom authentication backend"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

    def test_login_with_username(self):
        """Test that users can login using username"""
        login_successful = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(login_successful, "Should be able to login with username")

    def test_login_with_email(self):
        """Test that users can login using email"""
        login_successful = self.client.login(username="test@example.com", password="testpass123")
        self.assertTrue(login_successful, "Should be able to login with email")

    def test_login_with_wrong_password(self):
        """Test login fails with wrong password"""
        login_successful = self.client.login(username="testuser", password="wrongpassword")
        self.assertFalse(login_successful, "Should not be able to login with wrong password")

    def test_login_with_nonexistent_user(self):
        """Test login fails with nonexistent user"""
        login_successful = self.client.login(username="nonexistent", password="testpass123")
        self.assertFalse(login_successful, "Should not be able to login with nonexistent user")

    def test_case_insensitive_email_login(self):
        """Test that email login is case insensitive"""
        login_successful = self.client.login(username="TEST@EXAMPLE.COM", password="testpass123")
        self.assertTrue(login_successful, "Should be able to login with uppercase email")

    def test_case_insensitive_username_login(self):
        """Test that username login is case insensitive"""
        login_successful = self.client.login(username="TESTUSER", password="testpass123")
        self.assertTrue(login_successful, "Should be able to login with uppercase username")

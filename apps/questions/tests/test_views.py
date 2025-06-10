"""
Tests for Question views in HSK Exam System
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel

User = get_user_model()


class QuestionViewTestCase(TestCase):
    """Base test case for question views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Beginner level"
        )
        
        self.question_type = QuestionType.objects.create(
            name="Grammar",
            description="Grammar questions"
        )
        
        self.question = Question.objects.create(
            question_text="What is the correct grammar structure?",
            question_type=self.question_type,
            hsk_level=self.hsk_level,
            difficulty="medium",
            explanation="Test explanation",
            points=2
        )
        
        # Create choices
        self.choice1 = Choice.objects.create(
            question=self.question,
            choice_text="Option A",
            is_correct=False,
            order=0
        )
        self.choice2 = Choice.objects.create(
            question=self.question,
            choice_text="Option B",
            is_correct=True,
            order=1
        )
        
        self.question_bank = QuestionBank.objects.create(
            name="Test Bank",
            description="Test question bank",
            hsk_level=self.hsk_level
        )
        self.question_bank.questions.add(self.question)


class QuestionListViewTest(QuestionViewTestCase):
    """Test cases for QuestionListView"""
    
    def test_question_list_view_get(self):
        """Test GET request to question list view"""
        response = self.client.get(reverse('questions:list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question_text)
        self.assertContains(response, self.question_type.name)
        self.assertContains(response, f"HSK {self.hsk_level.level}")
    
    def test_question_list_view_search(self):
        """Test search functionality in question list"""
        response = self.client.get(reverse('questions:list'), {
            'search': 'grammar structure'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question_text)
    
    def test_question_list_view_filter_by_hsk_level(self):
        """Test filtering by HSK level"""
        response = self.client.get(reverse('questions:list'), {
            'hsk_level': self.hsk_level.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question_text)
    
    def test_question_list_view_filter_by_question_type(self):
        """Test filtering by question type"""
        response = self.client.get(reverse('questions:list'), {
            'question_type': self.question_type.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question_text)
    
    def test_question_list_view_filter_by_difficulty(self):
        """Test filtering by difficulty"""
        response = self.client.get(reverse('questions:list'), {
            'difficulty': 'medium'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question_text)
    
    def test_question_list_view_pagination(self):
        """Test pagination in question list"""
        # Create many questions
        for i in range(25):
            Question.objects.create(
                question_text=f"Test question {i}",
                question_type=self.question_type,
                hsk_level=self.hsk_level
            )
        
        response = self.client.get(reverse('questions:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])


class QuestionDetailViewTest(QuestionViewTestCase):
    """Test cases for QuestionDetailView"""
    
    def test_question_detail_view_get(self):
        """Test GET request to question detail view"""
        response = self.client.get(
            reverse('questions:detail', kwargs={'pk': self.question.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question.question_text)
        self.assertContains(response, self.question.explanation)
        self.assertContains(response, self.choice1.choice_text)
        self.assertContains(response, self.choice2.choice_text)
    
    def test_question_detail_view_nonexistent(self):
        """Test question detail view with nonexistent question"""
        response = self.client.get(
            reverse('questions:detail', kwargs={'pk': 9999})
        )
        
        self.assertEqual(response.status_code, 404)


class QuestionCreateViewTest(QuestionViewTestCase):
    """Test cases for QuestionCreateView"""
    
    def test_question_create_view_login_required(self):
        """Test that create view requires login"""
        response = self.client.get(reverse('questions:create'))
        self.assertRedirects(response, '/accounts/login/?next=/questions/create/')
    
    def test_question_create_view_get(self):
        """Test GET request to question create view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('questions:create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tạo câu hỏi mới')
    
    def test_question_create_view_post_valid(self):
        """Test POST request with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        form_data = {
            'question_text': 'New test question',
            'question_type': self.question_type.id,
            'hsk_level': self.hsk_level.id,
            'difficulty': 'easy',
            'points': 1,
            'is_active': True,
            
            # Formset management form
            'choices-TOTAL_FORMS': '2',
            'choices-INITIAL_FORMS': '0',
            'choices-MIN_NUM_FORMS': '2',
            'choices-MAX_NUM_FORMS': '6',
            
            # Choice data
            'choices-0-choice_text': 'Choice A',
            'choices-0-is_correct': False,
            'choices-0-order': 0,
            
            'choices-1-choice_text': 'Choice B',
            'choices-1-is_correct': True,
            'choices-1-order': 1,
        }
        
        response = self.client.post(reverse('questions:create'), form_data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Check question was created
        new_question = Question.objects.get(question_text='New test question')
        self.assertEqual(new_question.question_type, self.question_type)
        self.assertEqual(new_question.choices.count(), 2)
        self.assertTrue(new_question.choices.filter(is_correct=True).exists())


class QuestionUpdateViewTest(QuestionViewTestCase):
    """Test cases for QuestionUpdateView"""
    
    def test_question_update_view_login_required(self):
        """Test that update view requires login"""
        response = self.client.get(
            reverse('questions:edit', kwargs={'pk': self.question.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/questions/{self.question.pk}/edit/'
        )
    
    def test_question_update_view_get(self):
        """Test GET request to question update view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('questions:edit', kwargs={'pk': self.question.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sửa câu hỏi')
        self.assertContains(response, self.question.question_text)


class QuestionDeleteViewTest(QuestionViewTestCase):
    """Test cases for QuestionDeleteView"""
    
    def test_question_delete_view_login_required(self):
        """Test that delete view requires login"""
        response = self.client.get(
            reverse('questions:delete', kwargs={'pk': self.question.pk})
        )
        self.assertRedirects(
            response, 
            f'/accounts/login/?next=/questions/{self.question.pk}/delete/'
        )
    
    def test_question_delete_view_get(self):
        """Test GET request to question delete view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(
            reverse('questions:delete', kwargs={'pk': self.question.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Xác nhận xóa câu hỏi')
        self.assertContains(response, self.question.question_text)
    
    def test_question_delete_view_post(self):
        """Test POST request to delete question"""
        self.client.login(email='test@example.com', password='testpass123')
        question_id = self.question.pk
        
        response = self.client.post(
            reverse('questions:delete', kwargs={'pk': question_id})
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Check question was deleted
        self.assertFalse(Question.objects.filter(pk=question_id).exists())


class QuestionBankViewTest(QuestionViewTestCase):
    """Test cases for QuestionBank views"""
    
    def test_question_bank_list_view(self):
        """Test question bank list view"""
        response = self.client.get(reverse('questions:bank_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question_bank.name)
    
    def test_question_bank_detail_view(self):
        """Test question bank detail view"""
        response = self.client.get(
            reverse('questions:bank_detail', kwargs={'pk': self.question_bank.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.question_bank.name)
        self.assertContains(response, self.question.question_text)
    
    def test_question_bank_create_view_login_required(self):
        """Test that bank create view requires login"""
        response = self.client.get(reverse('questions:bank_create'))
        self.assertRedirects(response, '/accounts/login/?next=/questions/banks/create/')
    
    def test_question_bank_create_view_get(self):
        """Test GET request to bank create view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('questions:bank_create'))
        
        self.assertEqual(response.status_code, 200)


class ImportQuestionsViewTest(QuestionViewTestCase):
    """Test cases for import questions view"""
    
    def test_import_view_login_required(self):
        """Test that import view requires login"""
        response = self.client.get(reverse('questions:import'))
        self.assertRedirects(response, '/accounts/login/?next=/questions/import/')
    
    def test_import_view_get(self):
        """Test GET request to import view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('questions:import'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Import câu hỏi')
    
    def test_import_csv_valid(self):
        """Test importing valid CSV file"""
        self.client.login(email='test@example.com', password='testpass123')
        
        csv_content = """question_text,question_type,difficulty,passage,explanation,points,choice_A,choice_B,choice_C,choice_D,correct_answer
"Test CSV question","Vocabulary","easy","","Test explanation",1,"Option A","Option B","Option C","Option D","B"
"""
        
        csv_file = SimpleUploadedFile(
            "test_questions.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        form_data = {
            'file_type': 'csv',
            'file': csv_file,
            'hsk_level': self.hsk_level.id,
            'question_bank': self.question_bank.id,
            'overwrite_duplicates': False
        }
        
        response = self.client.post(reverse('questions:import'), form_data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Check question was created
        self.assertTrue(
            Question.objects.filter(question_text="Test CSV question").exists()
        )
    
    def test_import_json_valid(self):
        """Test importing valid JSON file"""
        self.client.login(email='test@example.com', password='testpass123')
        
        json_content = """{
  "questions": [
    {
      "question_text": "Test JSON question",
      "question_type": "Reading",
      "difficulty": "medium",
      "explanation": "Test explanation",
      "points": 2,
      "choices": [
        {"text": "Choice A", "is_correct": false},
        {"text": "Choice B", "is_correct": true}
      ]
    }
  ]
}"""
        
        json_file = SimpleUploadedFile(
            "test_questions.json",
            json_content.encode('utf-8'),
            content_type="application/json"
        )
        
        form_data = {
            'file_type': 'json',
            'file': json_file,
            'hsk_level': self.hsk_level.id,
            'create_new_bank': True,
            'new_bank_name': 'JSON Import Bank',
            'overwrite_duplicates': False
        }
        
        response = self.client.post(reverse('questions:import'), form_data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Check question was created
        self.assertTrue(
            Question.objects.filter(question_text="Test JSON question").exists()
        )
        
        # Check question bank was created
        self.assertTrue(
            QuestionBank.objects.filter(name="JSON Import Bank").exists()
        )

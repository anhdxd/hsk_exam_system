"""
Tests for Question forms in HSK Exam System
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.questions.forms import (
    QuestionForm, ChoiceForm, QuestionBankForm, 
    ImportForm, QuestionSearchForm
)
from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel


class QuestionFormTest(TestCase):
    """Test cases for QuestionForm"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
        self.question_type = QuestionType.objects.create(
            name="Grammar"
        )
    
    def test_question_form_valid_data(self):
        """Test QuestionForm with valid data"""
        form_data = {
            'question_text': 'What is the correct grammar?',
            'question_type': self.question_type.id,
            'hsk_level': self.hsk_level.id,
            'difficulty': 'medium',
            'points': 2,
            'is_active': True,
            'explanation': 'Test explanation'
        }
        
        form = QuestionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_question_form_required_fields(self):
        """Test QuestionForm with missing required fields"""
        form_data = {}
        
        form = QuestionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('question_text', form.errors)
        self.assertIn('question_type', form.errors)
        self.assertIn('hsk_level', form.errors)
    
    def test_question_form_reading_comprehension_validation(self):
        """Test validation for reading comprehension questions"""
        reading_type = QuestionType.objects.create(name="Reading Comprehension")
        
        form_data = {
            'question_text': 'Reading question',
            'question_type': reading_type.id,
            'hsk_level': self.hsk_level.id,
            'difficulty': 'medium',
            'points': 1,
            'is_active': True,
            # Missing passage for reading question
        }
        
        form = QuestionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('passage', form.errors)
    
    def test_question_form_listening_validation(self):
        """Test validation for listening questions"""
        listening_type = QuestionType.objects.create(name="Listening")
        
        form_data = {
            'question_text': 'Listening question',
            'question_type': listening_type.id,
            'hsk_level': self.hsk_level.id,
            'difficulty': 'medium',
            'points': 1,
            'is_active': True,
            # Missing audio_file for listening question
        }
        
        form = QuestionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('audio_file', form.errors)


class ChoiceFormTest(TestCase):
    """Test cases for ChoiceForm"""
    
    def test_choice_form_valid_data(self):
        """Test ChoiceForm with valid data"""
        form_data = {
            'choice_text': 'Option A',
            'is_correct': True,
            'order': 0
        }
        
        form = ChoiceForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_choice_form_required_fields(self):
        """Test ChoiceForm with missing required fields"""
        form_data = {}
        
        form = ChoiceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('choice_text', form.errors)


class QuestionBankFormTest(TestCase):
    """Test cases for QuestionBankForm"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
    
    def test_question_bank_form_valid_data(self):
        """Test QuestionBankForm with valid data"""
        form_data = {
            'name': 'Test Bank',
            'description': 'Test description',
            'hsk_level': self.hsk_level.id,
            'is_active': True
        }
        
        form = QuestionBankForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_question_bank_form_required_fields(self):
        """Test QuestionBankForm with missing required fields"""
        form_data = {}
        
        form = QuestionBankForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('hsk_level', form.errors)


class ImportFormTest(TestCase):
    """Test cases for ImportForm"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
        self.question_bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level
        )
    
    def test_import_form_csv_valid(self):
        """Test ImportForm with valid CSV data"""
        csv_file = SimpleUploadedFile(
            "test.csv",
            b"question_text,question_type\nTest,Grammar",
            content_type="text/csv"
        )
        
        form_data = {
            'file_type': 'csv',
            'hsk_level': self.hsk_level.id,
            'question_bank': self.question_bank.id,
            'overwrite_duplicates': False
        }
        
        form = ImportForm(data=form_data, files={'file': csv_file})
        self.assertTrue(form.is_valid())
    
    def test_import_form_json_valid(self):
        """Test ImportForm with valid JSON data"""
        json_file = SimpleUploadedFile(
            "test.json",
            b'{"questions": []}',
            content_type="application/json"
        )
        
        form_data = {
            'file_type': 'json',
            'hsk_level': self.hsk_level.id,
            'create_new_bank': True,
            'new_bank_name': 'New Bank',
            'overwrite_duplicates': False
        }
        
        form = ImportForm(data=form_data, files={'file': json_file})
        self.assertTrue(form.is_valid())
    
    def test_import_form_file_extension_validation(self):
        """Test file extension validation"""
        # Wrong extension for CSV
        wrong_file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        
        form_data = {
            'file_type': 'csv',
            'hsk_level': self.hsk_level.id,
            'question_bank': self.question_bank.id
        }
        
        form = ImportForm(data=form_data, files={'file': wrong_file})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
    
    def test_import_form_new_bank_validation(self):
        """Test validation when creating new bank"""
        csv_file = SimpleUploadedFile(
            "test.csv",
            b"test content",
            content_type="text/csv"
        )
        
        form_data = {
            'file_type': 'csv',
            'hsk_level': self.hsk_level.id,
            'create_new_bank': True,
            # Missing new_bank_name
            'overwrite_duplicates': False
        }
        
        form = ImportForm(data=form_data, files={'file': csv_file})
        self.assertFalse(form.is_valid())
        self.assertIn('new_bank_name', form.errors)
    
    def test_import_form_bank_selection_validation(self):
        """Test validation for bank selection"""
        csv_file = SimpleUploadedFile(
            "test.csv",
            b"test content",
            content_type="text/csv"
        )
        
        form_data = {
            'file_type': 'csv',
            'hsk_level': self.hsk_level.id,
            # Neither create_new_bank nor question_bank selected
            'overwrite_duplicates': False
        }
        
        form = ImportForm(data=form_data, files={'file': csv_file})
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)  # Non-field error


class QuestionSearchFormTest(TestCase):
    """Test cases for QuestionSearchForm"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
        self.question_type = QuestionType.objects.create(
            name="Grammar"
        )
    
    def test_question_search_form_valid(self):
        """Test QuestionSearchForm with valid data"""
        form_data = {
            'search': 'test query',
            'hsk_level': self.hsk_level.id,
            'question_type': self.question_type.id,
            'difficulty': 'medium',
            'is_active': 'true'
        }
        
        form = QuestionSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_question_search_form_empty(self):
        """Test QuestionSearchForm with empty data (all optional)"""
        form_data = {}
        
        form = QuestionSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_question_search_form_partial_data(self):
        """Test QuestionSearchForm with partial data"""
        form_data = {
            'search': 'grammar',
            'hsk_level': self.hsk_level.id
            # Other fields empty/None
        }
        
        form = QuestionSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


class FormIntegrationTest(TestCase):
    """Integration tests for forms working together"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
        self.question_type = QuestionType.objects.create(
            name="Grammar"
        )
    
    def test_question_and_choice_form_integration(self):
        """Test creating question with choices using forms"""
        # Create question
        question_data = {
            'question_text': 'Integration test question',
            'question_type': self.question_type.id,
            'hsk_level': self.hsk_level.id,
            'difficulty': 'easy',
            'points': 1,
            'is_active': True
        }
        
        question_form = QuestionForm(data=question_data)
        self.assertTrue(question_form.is_valid())
        
        question = question_form.save()
        
        # Create choices
        choice_data_1 = {
            'choice_text': 'Choice A',
            'is_correct': False,
            'order': 0
        }
        choice_data_2 = {
            'choice_text': 'Choice B',
            'is_correct': True,
            'order': 1
        }
        
        choice_form_1 = ChoiceForm(data=choice_data_1)
        choice_form_2 = ChoiceForm(data=choice_data_2)
        
        self.assertTrue(choice_form_1.is_valid())
        self.assertTrue(choice_form_2.is_valid())
        
        choice_1 = choice_form_1.save(commit=False)
        choice_1.question = question
        choice_1.save()
        
        choice_2 = choice_form_2.save(commit=False)
        choice_2.question = question
        choice_2.save()
        
        # Verify integration
        self.assertEqual(question.choices.count(), 2)
        self.assertTrue(question.choices.filter(is_correct=True).exists())
        self.assertEqual(question.get_correct_choice().choice_text, 'Choice B')

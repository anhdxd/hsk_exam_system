"""
Tests for Question import functionality in HSK Exam System
"""

import json
import tempfile
from io import StringIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.questions.import_questions import (
    QuestionImporter, 
    import_questions_from_csv,
    import_questions_from_json,
    create_sample_csv,
    create_sample_json
)
from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel


class QuestionImporterTest(TestCase):
    """Test cases for QuestionImporter class"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Beginner level"
        )
        
        self.question_bank = QuestionBank.objects.create(
            name="Test Bank",
            description="Test question bank",
            hsk_level=self.hsk_level
        )
        
        self.importer = QuestionImporter()
    
    def test_csv_import_valid(self):
        """Test importing valid CSV data"""
        csv_content = """question_text,question_type,difficulty,passage,explanation,points,choice_A,choice_B,choice_C,choice_D,correct_answer
"What is the meaning of '你好'?","Vocabulary","easy","","This is a basic greeting.",1,"Hello","Goodbye","Thank you","Excuse me","A"
"Choose the correct grammar.","Grammar","medium","","Subject + Verb + Object structure.",2,"我吃饭","吃我饭","饭吃我","我饭吃","A"
"""
        
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            csv_file, 'csv', self.hsk_level, self.question_bank
        )
        
        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify questions were created
        self.assertEqual(Question.objects.count(), 2)
        
        # Verify first question
        question1 = Question.objects.get(question_text__contains="你好")
        self.assertEqual(question1.question_type.name, "Vocabulary")
        self.assertEqual(question1.difficulty, "easy")
        self.assertEqual(question1.points, 1)
        self.assertEqual(question1.choices.count(), 4)
        self.assertTrue(question1.choices.filter(is_correct=True, choice_text="Hello").exists())
        
        # Verify question is in bank
        self.assertIn(question1, self.question_bank.questions.all())
    
    def test_csv_import_missing_required_fields(self):
        """Test CSV import with missing required fields"""
        csv_content = """question_text,question_type
"Incomplete question","Grammar"
"""
        
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            csv_file, 'csv', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
    
    def test_csv_import_invalid_correct_answer(self):
        """Test CSV import with invalid correct answer"""
        csv_content = """question_text,question_type,difficulty,passage,explanation,points,choice_A,choice_B,correct_answer
"Test question","Grammar","easy","","",1,"Choice A","Choice B","X"
"""
        
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            csv_file, 'csv', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
        self.assertTrue(
            any('Không tìm thấy lựa chọn cho đáp án đúng' in error for error in result['errors'])
        )
    
    def test_json_import_valid(self):
        """Test importing valid JSON data"""
        json_data = {
            "questions": [
                {
                    "question_text": "What does '谢谢' mean?",
                    "question_type": "Vocabulary",
                    "difficulty": "easy",
                    "explanation": "Basic politeness expression",
                    "points": 1,
                    "choices": [
                        {"text": "Thank you", "is_correct": True},
                        {"text": "Hello", "is_correct": False},
                        {"text": "Goodbye", "is_correct": False}
                    ]
                },
                {
                    "question_text": "Complete: 我___学生",
                    "question_type": "Grammar",
                    "difficulty": "medium",
                    "passage": "",
                    "explanation": "Use 是 to express 'to be'",
                    "points": 2,
                    "choices": [
                        {"text": "是", "is_correct": True},
                        {"text": "有", "is_correct": False},
                        {"text": "在", "is_correct": False},
                        {"text": "会", "is_correct": False}
                    ]
                }
            ]
        }
        
        json_file = SimpleUploadedFile(
            "test.json",
            json.dumps(json_data).encode('utf-8'),
            content_type="application/json"
        )
        
        result = self.importer.import_from_file(
            json_file, 'json', self.hsk_level, self.question_bank
        )
        
        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify questions were created
        self.assertEqual(Question.objects.count(), 2)
        
        # Verify first question
        question1 = Question.objects.get(question_text__contains="谢谢")
        self.assertEqual(question1.question_type.name, "Vocabulary")
        self.assertEqual(question1.choices.count(), 3)
        self.assertTrue(question1.choices.filter(is_correct=True, choice_text="Thank you").exists())
    
    def test_json_import_invalid_structure(self):
        """Test JSON import with invalid structure"""
        invalid_json = {"invalid": "structure"}
        
        json_file = SimpleUploadedFile(
            "test.json",
            json.dumps(invalid_json).encode('utf-8'),
            content_type="application/json"
        )
        
        result = self.importer.import_from_file(
            json_file, 'json', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
    
    def test_json_import_no_correct_answer(self):
        """Test JSON import with no correct answer"""
        json_data = {
            "questions": [
                {
                    "question_text": "Test question",
                    "question_type": "Test",
                    "choices": [
                        {"text": "Choice A", "is_correct": False},
                        {"text": "Choice B", "is_correct": False}
                    ]
                }
            ]
        }
        
        json_file = SimpleUploadedFile(
            "test.json",
            json.dumps(json_data).encode('utf-8'),
            content_type="application/json"
        )
        
        result = self.importer.import_from_file(
            json_file, 'json', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
        self.assertTrue(
            any('Phải có ít nhất một đáp án đúng' in error for error in result['errors'])
        )
    
    def test_json_import_multiple_correct_answers(self):
        """Test JSON import with multiple correct answers"""
        json_data = {
            "questions": [
                {
                    "question_text": "Test question",
                    "question_type": "Test",
                    "choices": [
                        {"text": "Choice A", "is_correct": True},
                        {"text": "Choice B", "is_correct": True}
                    ]
                }
            ]
        }
        
        json_file = SimpleUploadedFile(
            "test.json",
            json.dumps(json_data).encode('utf-8'),
            content_type="application/json"
        )
        
        result = self.importer.import_from_file(
            json_file, 'json', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
        self.assertTrue(
            any('Chỉ được có một đáp án đúng' in error for error in result['errors'])
        )
    
    def test_duplicate_handling_skip(self):
        """Test handling duplicates by skipping"""
        # Create existing question
        question_type = QuestionType.objects.create(name="Test Type")
        Question.objects.create(
            question_text="Duplicate question",
            question_type=question_type,
            hsk_level=self.hsk_level
        )
        
        csv_content = """question_text,question_type,choice_A,choice_B,correct_answer
"Duplicate question","Test Type","A","B","A"
"""
        
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            csv_file, 'csv', self.hsk_level, 
            overwrite_duplicates=False
        )
        
        self.assertEqual(result['created'], 0)  # Should skip duplicate
        self.assertEqual(Question.objects.count(), 1)  # Still only one
    
    def test_duplicate_handling_overwrite(self):
        """Test handling duplicates by overwriting"""
        # Create existing question
        question_type = QuestionType.objects.create(name="Test Type")
        existing_question = Question.objects.create(
            question_text="Duplicate question",
            question_type=question_type,
            hsk_level=self.hsk_level,
            difficulty="easy",
            points=1
        )
        
        csv_content = """question_text,question_type,difficulty,points,choice_A,choice_B,correct_answer
"Duplicate question","Test Type","hard","3","A","B","A"
"""
        
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            csv_file, 'csv', self.hsk_level,
            overwrite_duplicates=True
        )
        
        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 1)
        self.assertEqual(Question.objects.count(), 1)
        
        # Check if question was updated
        updated_question = Question.objects.get(pk=existing_question.pk)
        self.assertEqual(updated_question.difficulty, "hard")
        self.assertEqual(updated_question.points, 3)
    
    def test_unsupported_file_type(self):
        """Test importing unsupported file type"""
        dummy_file = SimpleUploadedFile(
            "test.txt",
            b"dummy content",
            content_type="text/plain"
        )
        
        result = self.importer.import_from_file(
            dummy_file, 'txt', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
        self.assertTrue(
            any('Unsupported file type' in error for error in result['errors'])
        )


class ConvenienceFunctionTest(TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
    
    def test_import_questions_from_csv_function(self):
        """Test import_questions_from_csv convenience function"""
        csv_content = """question_text,question_type,choice_A,choice_B,correct_answer
"Test question","Grammar","Option A","Option B","A"
"""
        
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        
        result = import_questions_from_csv(csv_file, self.hsk_level)
        
        self.assertEqual(result['created'], 1)
        self.assertEqual(len(result['errors']), 0)
    
    def test_import_questions_from_json_function(self):
        """Test import_questions_from_json convenience function"""
        json_data = {
            "questions": [
                {
                    "question_text": "Test question",
                    "question_type": "Grammar",
                    "choices": [
                        {"text": "Option A", "is_correct": True},
                        {"text": "Option B", "is_correct": False}
                    ]
                }
            ]
        }
        
        json_file = SimpleUploadedFile(
            "test.json",
            json.dumps(json_data).encode('utf-8'),
            content_type="application/json"
        )
        
        result = import_questions_from_json(json_file, self.hsk_level)
        
        self.assertEqual(result['created'], 1)
        self.assertEqual(len(result['errors']), 0)
    
    def test_create_sample_csv(self):
        """Test create_sample_csv function"""
        sample_csv = create_sample_csv()
        
        self.assertIsInstance(sample_csv, str)
        self.assertIn('question_text', sample_csv)
        self.assertIn('question_type', sample_csv)
        self.assertIn('correct_answer', sample_csv)
    
    def test_create_sample_json(self):
        """Test create_sample_json function"""
        sample_json = create_sample_json()
        
        self.assertIsInstance(sample_json, str)
        
        # Should be valid JSON
        try:
            data = json.loads(sample_json)
            self.assertIn('questions', data)
            self.assertIsInstance(data['questions'], list)
        except json.JSONDecodeError:
            self.fail("create_sample_json() did not return valid JSON")


class ImportErrorHandlingTest(TestCase):
    """Test cases for import error handling"""
    
    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(level=1, name="HSK 1")
        self.importer = QuestionImporter()
    
    def test_csv_encoding_error(self):
        """Test handling of CSV encoding errors"""
        # Create file with invalid encoding
        csv_file = SimpleUploadedFile(
            "test.csv",
            "question_text,question_type\nTést question,Grammar".encode('latin1'),
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            csv_file, 'csv', self.hsk_level
        )
        
        # Should handle encoding gracefully
        self.assertEqual(result['created'], 0)
        # May or may not have errors depending on fallback handling
    
    def test_json_parse_error(self):
        """Test handling of JSON parse errors"""
        invalid_json_file = SimpleUploadedFile(
            "test.json",
            b"{ invalid json syntax",
            content_type="application/json"
        )
        
        result = self.importer.import_from_file(
            invalid_json_file, 'json', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        self.assertGreater(len(result['errors']), 0)
        self.assertTrue(
            any('Lỗi định dạng JSON' in error for error in result['errors'])
        )
    
    def test_empty_file(self):
        """Test handling of empty files"""
        empty_csv_file = SimpleUploadedFile(
            "test.csv",
            b"",
            content_type="text/csv"
        )
        
        result = self.importer.import_from_file(
            empty_csv_file, 'csv', self.hsk_level
        )
        
        self.assertEqual(result['created'], 0)
        # Should handle empty file gracefully

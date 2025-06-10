"""
Import questions utility module for HSK Exam System
Handles importing questions from CSV and JSON files into the database
"""

import csv
import json
import io
from typing import Dict, List, Any, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel


class QuestionImporter:
    """Main class for importing questions from various file formats"""
    
    def __init__(self):
        self.created_count = 0
        self.updated_count = 0
        self.errors = []
    
    def import_from_file(self, file, file_type: str, hsk_level: HSKLevel, 
                        question_bank: QuestionBank = None, 
                        overwrite_duplicates: bool = False) -> Dict[str, Any]:
        """
        Import questions from uploaded file
        
        Args:
            file: Uploaded file object
            file_type: 'csv' or 'json'
            hsk_level: HSKLevel instance
            question_bank: Optional QuestionBank to add questions to
            overwrite_duplicates: Whether to overwrite existing questions
            
        Returns:
            Dict with results: {'created': int, 'updated': int, 'errors': list}
        """
        self.created_count = 0
        self.updated_count = 0
        self.errors = []
        
        try:
            with transaction.atomic():
                if file_type == 'csv':
                    self._import_from_csv(file, hsk_level, question_bank, overwrite_duplicates)
                elif file_type == 'json':
                    self._import_from_json(file, hsk_level, question_bank, overwrite_duplicates)
                else:
                    raise ValueError(f"Unsupported file type: {file_type}")
                    
        except Exception as e:
            self.errors.append(f"Lỗi tổng quát: {str(e)}")
        
        return {
            'created': self.created_count,
            'updated': self.updated_count,
            'errors': self.errors
        }
    
    def _import_from_csv(self, file, hsk_level: HSKLevel, 
                        question_bank: QuestionBank = None, 
                        overwrite_duplicates: bool = False):
        """Import questions from CSV file"""
        try:
            # Read and decode file
            file_content = file.read()
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8-sig')  # Handle BOM
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            # Validate required columns
            required_columns = ['question_text', 'question_type', 'choice_A', 'choice_B', 'correct_answer']
            missing_columns = [col for col in required_columns if col not in csv_reader.fieldnames]
            if missing_columns:
                raise ValueError(f"Thiếu các cột bắt buộc: {', '.join(missing_columns)}")
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    self._process_csv_row(row, row_num, hsk_level, question_bank, overwrite_duplicates)
                except Exception as e:
                    self.errors.append(f"Dòng {row_num}: {str(e)}")
                    
        except UnicodeDecodeError:
            self.errors.append("Lỗi encoding file. Vui lòng lưu file CSV với encoding UTF-8.")
        except Exception as e:
            self.errors.append(f"Lỗi đọc file CSV: {str(e)}")
    
    def _process_csv_row(self, row: Dict[str, str], row_num: int, 
                        hsk_level: HSKLevel, question_bank: QuestionBank = None,
                        overwrite_duplicates: bool = False):
        """Process a single CSV row"""
        # Extract and validate question data
        question_text = row.get('question_text', '').strip()
        if not question_text:
            raise ValueError("Nội dung câu hỏi không được để trống")
        
        question_type_name = row.get('question_type', '').strip()
        if not question_type_name:
            raise ValueError("Loại câu hỏi không được để trống")
        
        # Get or create question type
        question_type, created = QuestionType.objects.get_or_create(
            name=question_type_name,
            defaults={'description': f'Auto-created from CSV import'}
        )
        
        # Extract other fields
        difficulty = row.get('difficulty', 'medium').strip().lower()
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        
        passage = row.get('passage', '').strip()
        explanation = row.get('explanation', '').strip()
        
        try:
            points = int(row.get('points', 1))
            if points < 1 or points > 10:
                points = 1
        except (ValueError, TypeError):
            points = 1
        
        # Check for existing question
        existing_question = Question.objects.filter(
            question_text=question_text,
            hsk_level=hsk_level,
            question_type=question_type
        ).first()
        
        if existing_question and not overwrite_duplicates:
            return  # Skip duplicate
        
        # Create or update question
        question_data = {
            'question_text': question_text,
            'question_type': question_type,
            'hsk_level': hsk_level,
            'difficulty': difficulty,
            'passage': passage,
            'explanation': explanation,
            'points': points,
            'is_active': True
        }
        
        if existing_question and overwrite_duplicates:
            # Update existing question
            for field, value in question_data.items():
                setattr(existing_question, field, value)
            existing_question.save()
            question = existing_question
            self.updated_count += 1
        else:
            # Create new question
            question = Question.objects.create(**question_data)
            self.created_count += 1
        
        # Process choices
        self._process_csv_choices(row, question)
        
        # Add to question bank
        if question_bank:
            question_bank.questions.add(question)
    
    def _process_csv_choices(self, row: Dict[str, str], question: Question):
        """Process choices from CSV row"""
        # Clear existing choices
        question.choices.all().delete()
        
        # Get correct answer
        correct_answer = row.get('correct_answer', '').strip().upper()
        if not correct_answer:
            raise ValueError("Đáp án đúng không được để trống")
        
        # Process choices A, B, C, D, E, F
        choice_letters = ['A', 'B', 'C', 'D', 'E', 'F']
        choices_created = 0
        correct_choice_found = False
        
        for i, letter in enumerate(choice_letters):
            choice_text = row.get(f'choice_{letter}', '').strip()
            if choice_text:
                is_correct = (letter == correct_answer)
                if is_correct:
                    correct_choice_found = True
                
                Choice.objects.create(
                    question=question,
                    choice_text=choice_text,
                    is_correct=is_correct,
                    order=i
                )
                choices_created += 1
        
        if choices_created < 2:
            raise ValueError("Phải có ít nhất 2 lựa chọn")
        
        if not correct_choice_found:
            raise ValueError(f"Không tìm thấy lựa chọn cho đáp án đúng: {correct_answer}")
    
    def _import_from_json(self, file, hsk_level: HSKLevel, 
                         question_bank: QuestionBank = None,
                         overwrite_duplicates: bool = False):
        """Import questions from JSON file"""
        try:
            # Read and parse JSON
            file_content = file.read()
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            data = json.loads(file_content)
            
            # Handle different JSON structures
            if isinstance(data, dict) and 'questions' in data:
                questions_data = data['questions']
            elif isinstance(data, list):
                questions_data = data
            else:
                raise ValueError("JSON phải chứa mảng 'questions' hoặc là một mảng câu hỏi")
            
            if not isinstance(questions_data, list):
                raise ValueError("Dữ liệu câu hỏi phải là một mảng")
            
            for index, question_data in enumerate(questions_data):
                try:
                    self._process_json_question(question_data, index + 1, hsk_level, 
                                              question_bank, overwrite_duplicates)
                except Exception as e:
                    self.errors.append(f"Câu hỏi {index + 1}: {str(e)}")
                    
        except json.JSONDecodeError as e:
            self.errors.append(f"Lỗi định dạng JSON: {str(e)}")
        except Exception as e:
            self.errors.append(f"Lỗi đọc file JSON: {str(e)}")
    
    def _process_json_question(self, question_data: Dict[str, Any], index: int,
                              hsk_level: HSKLevel, question_bank: QuestionBank = None,
                              overwrite_duplicates: bool = False):
        """Process a single JSON question"""
        # Validate required fields
        if not isinstance(question_data, dict):
            raise ValueError("Dữ liệu câu hỏi phải là object")
        
        question_text = question_data.get('question_text', '').strip()
        if not question_text:
            raise ValueError("Nội dung câu hỏi không được để trống")
        
        question_type_name = question_data.get('question_type', '').strip()
        if not question_type_name:
            raise ValueError("Loại câu hỏi không được để trống")
        
        # Get or create question type
        question_type, created = QuestionType.objects.get_or_create(
            name=question_type_name,
            defaults={'description': f'Auto-created from JSON import'}
        )
        
        # Extract other fields
        difficulty = question_data.get('difficulty', 'medium')
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        
        passage = question_data.get('passage', '')
        explanation = question_data.get('explanation', '')
        points = question_data.get('points', 1)
        
        try:
            points = int(points)
            if points < 1 or points > 10:
                points = 1
        except (ValueError, TypeError):
            points = 1
        
        # Check for existing question
        existing_question = Question.objects.filter(
            question_text=question_text,
            hsk_level=hsk_level,
            question_type=question_type
        ).first()
        
        if existing_question and not overwrite_duplicates:
            return  # Skip duplicate
        
        # Create or update question
        question_fields = {
            'question_text': question_text,
            'question_type': question_type,
            'hsk_level': hsk_level,
            'difficulty': difficulty,
            'passage': passage,
            'explanation': explanation,
            'points': points,
            'is_active': True
        }
        
        if existing_question and overwrite_duplicates:
            for field, value in question_fields.items():
                setattr(existing_question, field, value)
            existing_question.save()
            question = existing_question
            self.updated_count += 1
        else:
            question = Question.objects.create(**question_fields)
            self.created_count += 1
        
        # Process choices
        choices_data = question_data.get('choices', [])
        if not isinstance(choices_data, list):
            raise ValueError("Choices phải là một mảng")
        
        self._process_json_choices(choices_data, question)
        
        # Add to question bank
        if question_bank:
            question_bank.questions.add(question)
    
    def _process_json_choices(self, choices_data: List[Dict[str, Any]], question: Question):
        """Process choices from JSON data"""
        # Clear existing choices
        question.choices.all().delete()
        
        if len(choices_data) < 2:
            raise ValueError("Phải có ít nhất 2 lựa chọn")
        
        if len(choices_data) > 6:
            raise ValueError("Tối đa 6 lựa chọn")
        
        correct_count = 0
        
        for i, choice_data in enumerate(choices_data):
            if not isinstance(choice_data, dict):
                raise ValueError(f"Lựa chọn {i + 1} phải là object")
            
            choice_text = choice_data.get('text', '').strip()
            if not choice_text:
                raise ValueError(f"Nội dung lựa chọn {i + 1} không được để trống")
            
            is_correct = bool(choice_data.get('is_correct', False))
            if is_correct:
                correct_count += 1
            
            Choice.objects.create(
                question=question,
                choice_text=choice_text,
                is_correct=is_correct,
                order=i
            )
        
        if correct_count == 0:
            raise ValueError("Phải có ít nhất một đáp án đúng")
        elif correct_count > 1:
            raise ValueError("Chỉ được có một đáp án đúng")


# Convenience functions
def import_questions_from_csv(file, hsk_level: HSKLevel, question_bank: QuestionBank = None,
                             overwrite_duplicates: bool = False) -> Dict[str, Any]:
    """Import questions from CSV file"""
    importer = QuestionImporter()
    return importer.import_from_file(file, 'csv', hsk_level, question_bank, overwrite_duplicates)


def import_questions_from_json(file, hsk_level: HSKLevel, question_bank: QuestionBank = None,
                              overwrite_duplicates: bool = False) -> Dict[str, Any]:
    """Import questions from JSON file"""
    importer = QuestionImporter()
    return importer.import_from_file(file, 'json', hsk_level, question_bank, overwrite_duplicates)


def create_sample_csv() -> str:
    """Create sample CSV content for demonstration"""
    return """question_text,question_type,difficulty,passage,explanation,points,choice_A,choice_B,choice_C,choice_D,correct_answer
"我今天______去学校。","Grammar",medium,"","在这个句子中，'去'是动词，表示去某个地方。",1,"会","要","能","可以",B
"下面哪个词的意思是'书'？","Vocabulary",easy,"","这是一个词汇选择题。",1,"本子","书本","笔记","作业",B"""


def create_sample_json() -> str:
    """Create sample JSON content for demonstration"""
    return """{
  "questions": [
    {
      "question_text": "我今天______去学校。",
      "question_type": "Grammar",
      "difficulty": "medium",
      "passage": "",
      "explanation": "在这个句子中，'去'是动词，表示去某个地方。",
      "points": 1,
      "choices": [
        {"text": "会", "is_correct": false},
        {"text": "要", "is_correct": true},
        {"text": "能", "is_correct": false},
        {"text": "可以", "is_correct": false}
      ]
    },
    {
      "question_text": "下面哪个词的意思是'书'？",
      "question_type": "Vocabulary", 
      "difficulty": "easy",
      "passage": "",
      "explanation": "这是一个词汇选择题。",
      "points": 1,
      "choices": [
        {"text": "本子", "is_correct": false},
        {"text": "书本", "is_correct": true},
        {"text": "笔记", "is_correct": false},
        {"text": "作业", "is_correct": false}
      ]
    }
  ]
}"""

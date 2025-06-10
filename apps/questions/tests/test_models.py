"""
Tests for Question models in HSK Exam System
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel

User = get_user_model()


class QuestionTypeModelTest(TestCase):
    """Test cases for QuestionType model"""

    def test_create_question_type(self):
        """Test creating a question type"""
        question_type = QuestionType.objects.create(
            name="Grammar",
            description="Grammar questions"
        )
        self.assertEqual(question_type.name, "Grammar")
        self.assertEqual(str(question_type), "Grammar")

    def test_unique_name_constraint(self):
        """Test that question type names must be unique"""
        QuestionType.objects.create(name="Vocabulary")

        with self.assertRaises(IntegrityError):
            QuestionType.objects.create(name="Vocabulary")


class QuestionModelTest(TestCase):
    """Test cases for Question model"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1",
            description="Beginner level"
        )
        self.question_type = QuestionType.objects.create(
            name="Grammar",
            description="Grammar questions"
        )

    def test_create_question(self):
        """Test creating a question"""
        question = Question.objects.create(
            question_text="What is the correct grammar?",
            question_type=self.question_type,
            hsk_level=self.hsk_level,
            difficulty="medium",
            points=2
        )

        self.assertEqual(question.question_text,
                         "What is the correct grammar?")
        self.assertEqual(question.question_type, self.question_type)
        self.assertEqual(question.hsk_level, self.hsk_level)
        self.assertEqual(question.difficulty, "medium")
        self.assertEqual(question.points, 2)
        self.assertTrue(question.is_active)

    def test_question_str_representation(self):
        """Test string representation of question"""
        question = Question.objects.create(
            question_text="This is a very long question text that should be truncated",
            question_type=self.question_type,
            hsk_level=self.hsk_level
        )

        expected = f"HSK{self.hsk_level.level} - {self.question_type.name} - This is a very long question text that should be t..."
        self.assertEqual(str(question), expected)

    def test_question_get_absolute_url(self):
        """Test get_absolute_url method"""
        question = Question.objects.create(
            question_text="Test question",
            question_type=self.question_type,
            hsk_level=self.hsk_level
        )

        expected_url = f"/questions/{question.pk}/"
        self.assertEqual(question.get_absolute_url(), expected_url)

    def test_question_difficulty_choices(self):
        """Test question difficulty validation"""
        question = Question.objects.create(
            question_text="Test question",
            question_type=self.question_type,
            hsk_level=self.hsk_level,
            difficulty="hard"
        )

        self.assertEqual(question.difficulty, "hard")

    def test_question_points_validation(self):
        """Test question points validation"""
        # Valid points
        question = Question.objects.create(
            question_text="Test question",
            question_type=self.question_type,
            hsk_level=self.hsk_level,
            points=5
        )
        self.assertEqual(question.points, 5)

        # Test model validation would need to be called explicitly
        question.points = 15  # Invalid value
        with self.assertRaises(ValidationError):
            question.full_clean()


class ChoiceModelTest(TestCase):
    """Test cases for Choice model"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=1,
            name="HSK 1"
        )
        self.question_type = QuestionType.objects.create(
            name="Vocabulary"
        )
        self.question = Question.objects.create(
            question_text="Choose the correct answer",
            question_type=self.question_type,
            hsk_level=self.hsk_level
        )

    def test_create_choice(self):
        """Test creating a choice"""
        choice = Choice.objects.create(
            question=self.question,
            choice_text="Option A",
            is_correct=True,
            order=0
        )

        self.assertEqual(choice.question, self.question)
        self.assertEqual(choice.choice_text, "Option A")
        self.assertTrue(choice.is_correct)
        self.assertEqual(choice.order, 0)

    def test_choice_str_representation(self):
        """Test string representation of choice"""
        choice = Choice.objects.create(
            question=self.question,
            choice_text="Correct answer",
            is_correct=True,
            order=0
        )

        expected = "Correct answer (✓)"
        self.assertEqual(str(choice), expected)

        choice.is_correct = False
        expected = "Correct answer (✗)"
        self.assertEqual(str(choice), expected)

    def test_get_choice_letter(self):
        """Test get_choice_letter method"""
        choice_a = Choice.objects.create(
            question=self.question,
            choice_text="Option A",
            order=0
        )
        choice_b = Choice.objects.create(
            question=self.question,
            choice_text="Option B",
            order=1
        )

        self.assertEqual(choice_a.get_choice_letter(), "A")
        self.assertEqual(choice_b.get_choice_letter(), "B")

    def test_unique_choice_order_per_question(self):
        """Test unique constraint for choice order per question"""
        Choice.objects.create(
            question=self.question,
            choice_text="Option A",
            order=0
        )

        # This should raise IntegrityError due to unique constraint
        with self.assertRaises(IntegrityError):
            Choice.objects.create(
                question=self.question,
                choice_text="Option B",
                order=0  # Same order as above
            )


class QuestionBankModelTest(TestCase):
    """Test cases for QuestionBank model"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(
            level=2,
            name="HSK 2"
        )

    def test_create_question_bank(self):
        """Test creating a question bank"""
        bank = QuestionBank.objects.create(
            name="HSK 2 Grammar Bank",
            description="Collection of HSK 2 grammar questions",
            hsk_level=self.hsk_level
        )

        self.assertEqual(bank.name, "HSK 2 Grammar Bank")
        self.assertEqual(bank.hsk_level, self.hsk_level)
        self.assertTrue(bank.is_active)

    def test_question_bank_str_representation(self):
        """Test string representation of question bank"""
        bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level
        )

        expected = f"Test Bank (HSK {self.hsk_level.level})"
        self.assertEqual(str(bank), expected)

    def test_question_bank_get_absolute_url(self):
        """Test get_absolute_url method"""
        bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level
        )

        expected_url = f"/questions/banks/{bank.pk}/"
        self.assertEqual(bank.get_absolute_url(), expected_url)

    def test_question_count_method(self):
        """Test question_count method"""
        bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level
        )

        # Initially no questions
        self.assertEqual(bank.question_count(), 0)

        # Add some questions
        question_type = QuestionType.objects.create(name="Test Type")
        question1 = Question.objects.create(
            question_text="Question 1",
            question_type=question_type,
            hsk_level=self.hsk_level
        )
        question2 = Question.objects.create(
            question_text="Question 2",
            question_type=question_type,
            hsk_level=self.hsk_level
        )

        bank.questions.add(question1, question2)
        self.assertEqual(bank.question_count(), 2)

    def test_questions_by_type_method(self):
        """Test questions_by_type method"""
        bank = QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level
        )

        # Create question types
        grammar_type = QuestionType.objects.create(name="Grammar")
        vocab_type = QuestionType.objects.create(name="Vocabulary")

        # Create questions
        grammar_q1 = Question.objects.create(
            question_text="Grammar Q1",
            question_type=grammar_type,
            hsk_level=self.hsk_level
        )
        grammar_q2 = Question.objects.create(
            question_text="Grammar Q2",
            question_type=grammar_type,
            hsk_level=self.hsk_level
        )
        vocab_q1 = Question.objects.create(
            question_text="Vocab Q1",
            question_type=vocab_type,
            hsk_level=self.hsk_level
        )

        bank.questions.add(grammar_q1, grammar_q2, vocab_q1)

        questions_by_type = bank.questions_by_type()

        # Convert to dict for easier testing
        result_dict = {item['question_type__name']: item['count']
                       for item in questions_by_type}

        self.assertEqual(result_dict['Grammar'], 2)
        self.assertEqual(result_dict['Vocabulary'], 1)

    def test_unique_question_bank_name_per_level(self):
        """Test unique constraint for bank name per HSK level"""
        QuestionBank.objects.create(
            name="Test Bank",
            hsk_level=self.hsk_level
        )

        # This should raise IntegrityError
        with self.assertRaises(IntegrityError):
            QuestionBank.objects.create(
                name="Test Bank",  # Same name
                hsk_level=self.hsk_level  # Same level
            )


class QuestionModelMethodsTest(TestCase):
    """Test cases for Question model methods"""

    def setUp(self):
        """Set up test data"""
        self.hsk_level = HSKLevel.objects.create(level=1, name="HSK 1")
        self.question_type = QuestionType.objects.create(name="Test Type")
        self.question = Question.objects.create(
            question_text="Test question",
            question_type=self.question_type,
            hsk_level=self.hsk_level
        )

    def test_get_correct_choice(self):
        """Test get_correct_choice method"""
        # Create choices
        choice1 = Choice.objects.create(
            question=self.question,
            choice_text="Wrong answer",
            is_correct=False,
            order=0
        )
        choice2 = Choice.objects.create(
            question=self.question,
            choice_text="Correct answer",
            is_correct=True,
            order=1
        )

        correct_choice = self.question.get_correct_choice()
        self.assertEqual(correct_choice, choice2)

    def test_get_correct_choice_none(self):
        """Test get_correct_choice when no correct choice exists"""
        Choice.objects.create(
            question=self.question,
            choice_text="Wrong answer",
            is_correct=False,
            order=0
        )

        correct_choice = self.question.get_correct_choice()
        self.assertIsNone(correct_choice)

    def test_get_choices(self):
        """Test get_choices method"""
        choice1 = Choice.objects.create(
            question=self.question,
            choice_text="Choice A",
            order=0
        )
        choice2 = Choice.objects.create(
            question=self.question,
            choice_text="Choice B",
            order=1
        )

        choices = self.question.get_choices()
        self.assertEqual(list(choices), [choice1, choice2])

        # Test ordering
        self.assertEqual(choices[0].order, 0)
        self.assertEqual(choices[1].order, 1)

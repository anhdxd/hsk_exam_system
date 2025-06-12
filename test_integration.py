#!/usr/bin/env python
"""
Test script to verify the integration of submissions functionality into exams app
"""
import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.exams.models import Exam, ExamSession, ExamAnswer
from apps.common.models import HSKLevel
from apps.questions.models import QuestionBank, Question, QuestionType, Choice

User = get_user_model()

def test_submission_integration():
    """Test the integrated submission functionality"""
    print("Testing submission integration in exams app...")
    
    # Test 1: Check if ExamAnswer model is accessible
    try:
        exam_answer_count = ExamAnswer.objects.count()
        print(f"✓ ExamAnswer model accessible - {exam_answer_count} records found")
    except Exception as e:
        print(f"✗ Error accessing ExamAnswer model: {e}")
        return False
    
    # Test 2: Check if models are properly related
    try:
        # Get first exam session if exists
        session = ExamSession.objects.first()
        if session:
            answers = session.exam_answers.all()
            print(f"✓ ExamSession.exam_answers relationship working - {answers.count()} answers found")
        else:
            print("ℹ No exam sessions found for relationship test")
    except Exception as e:
        print(f"✗ Error testing relationships: {e}")
        return False
    
    # Test 3: Check submission views are accessible
    try:
        from apps.exams.views import submission_history_view, submission_detail_view
        print("✓ Submission views imported successfully")
    except Exception as e:
        print(f"✗ Error importing submission views: {e}")
        return False
    
    # Test 4: Check utility functions
    try:
        from apps.exams.utils import (
            generate_random_questions, 
            distribute_questions_by_type,
            get_exam_statistics,
            validate_exam_configuration
        )
        print("✓ Utility functions imported successfully")
    except Exception as e:
        print(f"✗ Error importing utility functions: {e}")
        return False
    
    # Test 5: Check admin integration
    try:
        from apps.exams.admin import ExamAnswerAdmin
        print("✓ ExamAnswer admin configuration imported successfully")
    except Exception as e:
        print(f"✗ Error importing admin configuration: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    return True

def main():
    """Main test function"""
    print("=" * 60)
    print("HSK Exam System - Submission Integration Test")
    print("=" * 60)
    
    success = test_submission_integration()
    
    if success:
        print("\n✅ Integration test completed successfully!")
        print("The submissions app functionality has been successfully integrated into exams app.")
    else:
        print("\n❌ Integration test failed!")
        print("Please check the errors above and fix them.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

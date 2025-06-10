"""
Sample data creation script for Questions app
"""
import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel

def create_sample_questions():
    """Create sample questions for testing"""
    
    # Get question types and HSK levels
    grammar_type = QuestionType.objects.get(name="Ngữ pháp")
    vocab_type = QuestionType.objects.get(name="Từ vựng")
    reading_type = QuestionType.objects.get(name="Đọc hiểu")
    
    hsk1 = HSKLevel.objects.get(level=1)
    hsk2 = HSKLevel.objects.get(level=2)
    hsk3 = HSKLevel.objects.get(level=3)
    
    # Create sample questions
    questions_data = [
        {
            'question_text': '你好，我___李明。',
            'question_type': grammar_type,
            'hsk_level': hsk1,
            'difficulty': 'easy',
            'points': 1,
            'explanation': '这是基本的自我介绍句型，使用"是"来连接主语和宾语。',
            'choices': [
                {'text': '是', 'is_correct': True, 'order': 0},
                {'text': '在', 'is_correct': False, 'order': 1},
                {'text': '有', 'is_correct': False, 'order': 2},
                {'text': '叫', 'is_correct': False, 'order': 3},
            ]
        },
        {
            'question_text': '这个苹果___红色的。',
            'question_type': grammar_type,
            'hsk_level': hsk1,
            'difficulty': 'easy',
            'points': 1,
            'explanation': '形容词作谓语时需要用"是"字连接。',
            'choices': [
                {'text': '是', 'is_correct': True, 'order': 0},
                {'text': '在', 'is_correct': False, 'order': 1},
                {'text': '有', 'is_correct': False, 'order': 2},
                {'text': '很', 'is_correct': False, 'order': 3},
            ]
        },
        {
            'question_text': '"学校"的意思是：',
            'question_type': vocab_type,
            'hsk_level': hsk1,
            'difficulty': 'easy',
            'points': 1,
            'explanation': '"学校"是指学习的地方，即school。',
            'choices': [
                {'text': 'School', 'is_correct': True, 'order': 0},
                {'text': 'Hospital', 'is_correct': False, 'order': 1},
                {'text': 'Restaurant', 'is_correct': False, 'order': 2},
                {'text': 'Park', 'is_correct': False, 'order': 3},
            ]
        },
        {
            'question_text': '他每天___上班。',
            'question_type': grammar_type,
            'hsk_level': hsk2,
            'difficulty': 'medium',
            'points': 2,
            'explanation': '表示交通方式时用"坐"。',
            'choices': [
                {'text': '坐地铁', 'is_correct': True, 'order': 0},
                {'text': '坐着地铁', 'is_correct': False, 'order': 1},
                {'text': '在地铁', 'is_correct': False, 'order': 2},
                {'text': '用地铁', 'is_correct': False, 'order': 3},
            ]
        },
        {
            'question_text': '根据文章内容，小王今天做了什么？',
            'question_type': reading_type,
            'hsk_level': hsk2,
            'difficulty': 'medium',
            'points': 3,
            'passage': '今天是周末，小王起得很早。他先去买菜，然后回家做饭。下午，他和朋友一起看电影。晚上，他在家看书。',
            'explanation': '文章中提到小王买菜、做饭、看电影、看书。',
            'choices': [
                {'text': '买菜、做饭、看电影、看书', 'is_correct': True, 'order': 0},
                {'text': '只是买菜和做饭', 'is_correct': False, 'order': 1},
                {'text': '只是看电影', 'is_correct': False, 'order': 2},
                {'text': '睡觉和看书', 'is_correct': False, 'order': 3},
            ]
        },
        {
            'question_text': '虽然___很忙，但是他还是来帮助我们了。',
            'question_type': grammar_type,
            'hsk_level': hsk3,
            'difficulty': 'hard',
            'points': 3,
            'explanation': '"虽然...但是..."句式中，第一部分说明让步条件。',
            'choices': [
                {'text': '他', 'is_correct': True, 'order': 0},
                {'text': '我们', 'is_correct': False, 'order': 1},
                {'text': '工作', 'is_correct': False, 'order': 2},
                {'text': '时间', 'is_correct': False, 'order': 3},
            ]
        }
    ]
    
    created_questions = []
    
    for q_data in questions_data:
        # Create question
        choices_data = q_data.pop('choices')
        question = Question.objects.create(**q_data)
        
        # Create choices
        for choice_data in choices_data:
            Choice.objects.create(
                question=question,
                choice_text=choice_data['text'],
                is_correct=choice_data['is_correct'],
                order=choice_data['order']
            )
        
        created_questions.append(question)
        print(f"Created question: {question.question_text[:50]}...")
    
    # Create sample question banks
    banks_data = [
        {
            'name': 'HSK 1 基础练习',
            'description': 'HSK 1级别的基础语法和词汇练习题',
            'hsk_level': hsk1,
            'questions': [q for q in created_questions if q.hsk_level == hsk1]
        },
        {
            'name': 'HSK 2 综合练习',
            'description': 'HSK 2级别的综合练习，包含语法、词汇和阅读',
            'hsk_level': hsk2,
            'questions': [q for q in created_questions if q.hsk_level == hsk2]
        },
        {
            'name': 'HSK 3 高级练习',
            'description': 'HSK 3级别的高级语法练习',
            'hsk_level': hsk3,
            'questions': [q for q in created_questions if q.hsk_level == hsk3]
        }
    ]
    
    for bank_data in banks_data:
        questions = bank_data.pop('questions')
        bank = QuestionBank.objects.create(**bank_data)
        bank.questions.set(questions)
        print(f"Created question bank: {bank.name} with {bank.question_count()} questions")
    
    print(f"\nSample data creation completed!")
    print(f"Total questions created: {len(created_questions)}")
    print(f"Total question banks created: {len(banks_data)}")

if __name__ == "__main__":
    create_sample_questions()

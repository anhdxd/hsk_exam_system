from django.core.management.base import BaseCommand
from apps.common.models import HSKLevel
from apps.questions.models import QuestionType, Question, Choice, QuestionBank
from apps.exams.models import Exam


class Command(BaseCommand):
    help = 'Populate initial data for HSK Exam System'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate initial data...'))
        
        # Create HSK Levels
        self.create_hsk_levels()
        
        # Create Question Types
        self.create_question_types()
        
        # Create sample questions and question banks
        self.create_sample_questions()
        
        # Create sample exams
        self.create_sample_exams()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated initial data!'))

    def create_hsk_levels(self):
        """Create HSK levels 1-6"""
        hsk_data = [
            {'level': 1, 'name': 'HSK 1', 'description': 'Beginner level', 'vocabulary_count': 150},
            {'level': 2, 'name': 'HSK 2', 'description': 'Elementary level', 'vocabulary_count': 300},
            {'level': 3, 'name': 'HSK 3', 'description': 'Intermediate level', 'vocabulary_count': 600},
            {'level': 4, 'name': 'HSK 4', 'description': 'Upper intermediate level', 'vocabulary_count': 1200},
            {'level': 5, 'name': 'HSK 5', 'description': 'Advanced level', 'vocabulary_count': 2500},
            {'level': 6, 'name': 'HSK 6', 'description': 'Superior level', 'vocabulary_count': 5000},
        ]
        
        for data in hsk_data:
            hsk_level, created = HSKLevel.objects.get_or_create(
                level=data['level'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'vocabulary_count': data['vocabulary_count']
                }
            )
            if created:
                self.stdout.write(f'Created HSK Level {hsk_level.level}')
            else:
                self.stdout.write(f'HSK Level {hsk_level.level} already exists')

    def create_question_types(self):
        """Create different types of HSK questions"""
        question_types = [
            {'name': 'Listening Comprehension', 'description': 'Questions based on audio content'},
            {'name': 'Reading Comprehension', 'description': 'Questions based on reading passages'},
            {'name': 'Vocabulary', 'description': 'Vocabulary and word usage questions'},
            {'name': 'Grammar', 'description': 'Grammar structure questions'},
            {'name': 'Writing', 'description': 'Writing composition questions'},
            {'name': 'Speaking', 'description': 'Oral expression questions'},
        ]
        
        for data in question_types:
            question_type, created = QuestionType.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            if created:
                self.stdout.write(f'Created question type: {question_type.name}')

    def create_sample_questions(self):
        """Create sample questions for testing"""
        hsk1 = HSKLevel.objects.get(level=1)
        hsk2 = HSKLevel.objects.get(level=2)
        vocab_type = QuestionType.objects.get(name='Vocabulary')
        grammar_type = QuestionType.objects.get(name='Grammar')
        
        # HSK 1 Vocabulary Questions
        hsk1_questions = [
            {
                'question_text': '这是____？(What is this?)',
                'choices': [
                    {'text': '书', 'correct': True},
                    {'text': '车', 'correct': False},
                    {'text': '水', 'correct': False},
                    {'text': '人', 'correct': False},
                ],
                'explanation': '书 means "book" in Chinese.',
                'type': vocab_type,
                'level': hsk1
            },
            {
                'question_text': '我____中国人。(I am Chinese.)',
                'choices': [
                    {'text': '是', 'correct': True},
                    {'text': '有', 'correct': False},
                    {'text': '在', 'correct': False},
                    {'text': '去', 'correct': False},
                ],
                'explanation': '是 is the verb "to be" in Chinese.',
                'type': grammar_type,
                'level': hsk1
            },
            {
                'question_text': '你____吗？(Are you good?)',
                'choices': [
                    {'text': '好', 'correct': True},
                    {'text': '坏', 'correct': False},
                    {'text': '大', 'correct': False},
                    {'text': '小', 'correct': False},
                ],
                'explanation': '好 means "good" or "well".',
                'type': vocab_type,
                'level': hsk1
            }
        ]
        
        # HSK 2 Questions
        hsk2_questions = [
            {
                'question_text': '我昨天____了一本书。(I bought a book yesterday.)',
                'choices': [
                    {'text': '买', 'correct': True},
                    {'text': '卖', 'correct': False},
                    {'text': '看', 'correct': False},
                    {'text': '写', 'correct': False},
                ],
                'explanation': '买 means "to buy".',
                'type': vocab_type,
                'level': hsk2
            },
            {
                'question_text': '他比我____。(He is taller than me.)',
                'choices': [
                    {'text': '高', 'correct': True},
                    {'text': '矮', 'correct': False},
                    {'text': '胖', 'correct': False},
                    {'text': '瘦', 'correct': False},
                ],
                'explanation': '高 means "tall" or "high".',
                'type': grammar_type,
                'level': hsk2
            }
        ]
        
        all_questions = hsk1_questions + hsk2_questions
        
        for q_data in all_questions:
            question, created = Question.objects.get_or_create(
                question_text=q_data['question_text'],
                defaults={
                    'question_type': q_data['type'],
                    'hsk_level': q_data['level'],
                    'difficulty': 'easy',
                    'explanation': q_data['explanation'],
                    'points': 1
                }
            )
            
            if created:
                self.stdout.write(f'Created question: {question.question_text[:30]}...')
                
                # Create choices for the question
                for i, choice_data in enumerate(q_data['choices']):
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_data['text'],
                        is_correct=choice_data['correct'],
                        order=i
                    )

        # Create Question Banks
        self.create_question_banks()

    def create_question_banks(self):
        """Create question banks for each HSK level"""
        for level in range(1, 3):  # Only create for levels 1 and 2 for now
            hsk_level = HSKLevel.objects.get(level=level)
            questions = Question.objects.filter(hsk_level=hsk_level)
            
            if questions.exists():
                bank, created = QuestionBank.objects.get_or_create(
                    name=f'HSK {level} Question Bank',
                    defaults={
                        'description': f'Complete question bank for HSK Level {level}',
                        'hsk_level': hsk_level,
                        'is_active': True
                    }
                )
                
                if created:
                    bank.questions.set(questions)
                    self.stdout.write(f'Created question bank for HSK {level} with {questions.count()} questions')

    def create_sample_exams(self):
        """Create sample exams"""
        for level in range(1, 3):  # Only create for levels 1 and 2
            hsk_level = HSKLevel.objects.get(level=level)
            question_bank = QuestionBank.objects.filter(hsk_level=hsk_level).first()
            
            if question_bank:
                exam, created = Exam.objects.get_or_create(
                    title=f'HSK {level} Practice Exam',
                    defaults={
                        'description': f'Practice exam for HSK Level {level}',
                        'hsk_level': hsk_level,
                        'question_bank': question_bank,
                        'duration_minutes': 60 if level == 1 else 90,
                        'total_questions': question_bank.questions.count(),
                        'passing_score': 60.0,
                        'is_active': True,
                        'randomize_questions': True,
                        'show_results_immediately': True,
                        'allow_retake': True,
                        'max_attempts': 3
                    }
                )
                
                if created:
                    self.stdout.write(f'Created exam: {exam.title}')

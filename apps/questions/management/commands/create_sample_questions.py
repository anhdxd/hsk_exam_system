"""
Management command to create sample questions for testing
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.questions.models import Question, Choice, QuestionType, QuestionBank
from apps.common.models import HSKLevel


class Command(BaseCommand):
    help = 'Create sample questions for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sample questions to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(f'Creating {count} sample questions...')
        
        try:
            with transaction.atomic():
                created_count = self.create_sample_questions(count)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created {created_count} sample questions'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample questions: {e}')
            )

    def create_sample_questions(self, count):
        """Create sample questions with choices"""
        # Get or create question types and HSK levels
        question_types = list(QuestionType.objects.all())
        hsk_levels = list(HSKLevel.objects.all())
        
        if not question_types:
            self.stdout.write(
                self.style.WARNING('No question types found. Please load fixtures first.')
            )
            return 0
            
        if not hsk_levels:
            self.stdout.write(
                self.style.WARNING('No HSK levels found. Please load fixtures first.')
            )
            return 0

        # Sample questions data
        sample_questions = [
            {
                'text': '选择正确的拼音：你好',
                'type': '从 vocabulary',
                'choices': ['nǐ hǎo', 'nǐ háo', 'ní hǎo', 'nǐ hào'],
                'correct': 0,
                'explanation': '"你好"的正确拼音是"nǐ hǎo"，其中"你"是第三声，"好"是第三声。'
            },
            {
                'text': '下面哪个句子是正确的？',
                'type': 'grammar',
                'choices': ['我是学生', '我是一个学生', '我是的学生', '我是在学生'],
                'correct': 1,
                'explanation': '正确的表达是"我是一个学生"，需要使用量词"一个"。'
            },
            {
                'text': '"谢谢"的意思是什么？',
                'type': 'vocabulary',
                'choices': ['你好', '再见', '感谢', '对不起'],
                'correct': 2,
                'explanation': '"谢谢"表示感谢、感激的意思。'
            },
            {
                'text': '选择正确的语序：我/昨天/看/了/一部/电影',
                'type': 'grammar',
                'choices': ['我昨天看了一部电影', '我看了昨天一部电影', '昨天我看了一部电影', '我一部电影昨天看了'],
                'correct': 0,
                'explanation': '中文的基本语序是主语+时间+动词+宾语，所以正确答案是"我昨天看了一部电影"。'
            },
            {
                'text': '"家"的拼音是什么？',
                'type': 'vocabulary',
                'choices': ['jiā', 'jiá', 'jiǎ', 'jià'],
                'correct': 0,
                'explanation': '"家"的正确拼音是"jiā"，第一声。'
            },
            {
                'text': '哪个词表示"水果"？',
                'type': 'vocabulary',
                'choices': ['蔬菜', '水果', '饮料', '零食'],
                'correct': 1,
                'explanation': '"水果"就是表示各种水果的词汇。'
            },
            {
                'text': '选择正确的量词：一___书',
                'type': 'grammar',
                'choices': ['个', '本', '张', '只'],
                'correct': 1,
                'explanation': '书的量词是"本"，所以是"一本书"。'
            },
            {
                'text': '"早上好"什么时候说？',
                'type': 'vocabulary',
                'choices': ['晚上', '中午', '早上', '下午'],
                'correct': 2,
                'explanation': '"早上好"是早上见面时的问候语。'
            },
            {
                'text': '哪个是正确的否定句？',
                'type': 'grammar',
                'choices': ['我不是学生', '我没是学生', '我不在学生', '我没有是学生'],
                'correct': 0,
                'explanation': '否定"是"用"不是"，所以正确答案是"我不是学生"。'
            },
            {
                'text': '"再见"的英文是什么意思？',
                'type': 'vocabulary',
                'choices': ['Hello', 'Thank you', 'Goodbye', 'Sorry'],
                'correct': 2,
                'explanation': '"再见"的英文意思是"Goodbye"。'
            },
        ]

        created_count = 0
        difficulties = ['easy', 'medium', 'hard']
        
        for i in range(count):
            # Cycle through sample questions
            sample = sample_questions[i % len(sample_questions)]
            
            # Determine question type
            qt_name = sample['type']
            if 'vocabulary' in qt_name.lower() or 'vocab' in qt_name.lower():
                question_type = next((qt for qt in question_types if 'từ vựng' in qt.name.lower()), question_types[0])
            elif 'grammar' in qt_name.lower():
                question_type = next((qt for qt in question_types if 'ngữ pháp' in qt.name.lower()), question_types[0])
            else:
                question_type = question_types[i % len(question_types)]
            
            # Cycle through HSK levels
            hsk_level = hsk_levels[i % len(hsk_levels)]
            difficulty = difficulties[i % len(difficulties)]
            
            # Create question
            question = Question.objects.create(
                question_text=f"{sample['text']} (Câu {i+1})",
                question_type=question_type,
                hsk_level=hsk_level,
                difficulty=difficulty,
                points=hsk_level.level,  # Points based on HSK level
                explanation=sample.get('explanation', ''),
                is_active=True
            )
            
            # Create choices
            for j, choice_text in enumerate(sample['choices']):
                Choice.objects.create(
                    question=question,
                    choice_text=choice_text,
                    is_correct=(j == sample['correct']),
                    order=j
                )
            
            created_count += 1
            
            if created_count % 5 == 0:
                self.stdout.write(f'Created {created_count} questions...')
        
        # Create some question banks
        self.create_sample_banks()
        
        return created_count

    def create_sample_banks(self):
        """Create sample question banks"""
        self.stdout.write('Creating sample question banks...')
        
        for hsk_level in HSKLevel.objects.all():
            # Create vocabulary bank
            vocab_bank, created = QuestionBank.objects.get_or_create(
                name=f"Ngân hàng từ vựng HSK {hsk_level.level}",
                hsk_level=hsk_level,
                defaults={
                    'description': f'Tập hợp câu hỏi từ vựng cho HSK cấp độ {hsk_level.level}'
                }
            )
            
            if created:
                # Add vocabulary questions to this bank
                vocab_questions = Question.objects.filter(
                    hsk_level=hsk_level,
                    question_type__name__icontains='từ vựng'
                )[:5]  # Limit to 5 questions
                vocab_bank.questions.add(*vocab_questions)
            
            # Create grammar bank
            grammar_bank, created = QuestionBank.objects.get_or_create(
                name=f"Ngân hàng ngữ pháp HSK {hsk_level.level}",
                hsk_level=hsk_level,
                defaults={
                    'description': f'Tập hợp câu hỏi ngữ pháp cho HSK cấp độ {hsk_level.level}'
                }
            )
            
            if created:
                # Add grammar questions to this bank
                grammar_questions = Question.objects.filter(
                    hsk_level=hsk_level,
                    question_type__name__icontains='ngữ pháp'
                )[:5]  # Limit to 5 questions
                grammar_bank.questions.add(*grammar_questions)
        
        self.stdout.write('Sample question banks created.')

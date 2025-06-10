from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
import json
import csv
import io

from .models import Question, QuestionBank, Choice, QuestionType
from .forms import (
    QuestionForm, ChoiceFormSet, QuestionBankForm, 
    ImportForm, QuestionSearchForm, QuestionBankSearchForm
)
from .import_questions import QuestionImporter
from apps.common.models import HSKLevel


class QuestionListView(ListView):
    """List view for questions with search and filtering"""
    model = Question
    template_name = 'questions/question_list.html'
    context_object_name = 'questions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Question.objects.select_related(
            'question_type', 'hsk_level'
        ).prefetch_related('choices')
        
        # Get search parameters
        search = self.request.GET.get('search')
        hsk_level = self.request.GET.get('hsk_level')
        question_type = self.request.GET.get('question_type')
        difficulty = self.request.GET.get('difficulty')
        is_active = self.request.GET.get('is_active')
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(question_text__icontains=search) |
                Q(explanation__icontains=search) |
                Q(passage__icontains=search)
            )
        
        if hsk_level:
            queryset = queryset.filter(hsk_level_id=hsk_level)
        
        if question_type:
            queryset = queryset.filter(question_type_id=question_type)
        
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = QuestionSearchForm(self.request.GET)
        context['total_questions'] = self.get_queryset().count()
        return context


class QuestionDetailView(DetailView):
    """Detail view for a single question"""
    model = Question
    template_name = 'questions/question_detail.html'
    context_object_name = 'question'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['choices'] = self.object.get_choices()
        context['correct_choice'] = self.object.get_correct_choice()
        return context


class QuestionCreateView(LoginRequiredMixin, CreateView):
    """Create view for questions"""
    model = Question
    form_class = QuestionForm
    template_name = 'questions/question_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ChoiceFormSet(self.request.POST)
        else:
            context['formset'] = ChoiceFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            # Validate that at least one correct answer exists
            correct_choices = self.object.choices.filter(is_correct=True).count()
            if correct_choices == 0:
                messages.error(
                    self.request, 
                    'Phải có ít nhất một đáp án đúng cho câu hỏi!'
                )
                return self.form_invalid(form)
            elif correct_choices > 1:
                messages.error(
                    self.request, 
                    'Chỉ được có một đáp án đúng cho câu hỏi!'
                )
                return self.form_invalid(form)
            
            messages.success(
                self.request, 
                f'Câu hỏi "{self.object}" đã được tạo thành công!'
            )
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for questions"""
    model = Question
    form_class = QuestionForm
    template_name = 'questions/question_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ChoiceFormSet(
                self.request.POST, 
                instance=self.object
            )
        else:
            context['formset'] = ChoiceFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.save()
            
            # Validate that at least one correct answer exists
            correct_choices = self.object.choices.filter(is_correct=True).count()
            if correct_choices == 0:
                messages.error(
                    self.request, 
                    'Phải có ít nhất một đáp án đúng cho câu hỏi!'
                )
                return self.form_invalid(form)
            elif correct_choices > 1:
                messages.error(
                    self.request, 
                    'Chỉ được có một đáp án đúng cho câu hỏi!'
                )
                return self.form_invalid(form)
            
            messages.success(
                self.request, 
                f'Câu hỏi "{self.object}" đã được cập nhật!'
            )
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for questions"""
    model = Question
    template_name = 'questions/question_confirm_delete.html'
    success_url = reverse_lazy('questions:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(
            request, 
            f'Câu hỏi "{self.get_object()}" đã được xóa!'
        )
        return super().delete(request, *args, **kwargs)


# QuestionBank Views
class QuestionBankListView(ListView):
    """List view for question banks"""
    model = QuestionBank
    template_name = 'questions/questionbank_list.html'
    context_object_name = 'object_list'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = QuestionBank.objects.select_related('hsk_level').annotate(
            question_count=Count('questions')
        )
        
        # Apply filters
        hsk_level = self.request.GET.get('hsk_level')
        search = self.request.GET.get('search')
        
        if hsk_level:
            queryset = queryset.filter(hsk_level_id=hsk_level)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hsk_levels'] = HSKLevel.objects.all().order_by('level')
        context['search_form'] = QuestionBankSearchForm(self.request.GET)
        return context


class QuestionBankDetailView(DetailView):
    """Detail view for question bank"""
    model = QuestionBank
    template_name = 'questions/questionbank_detail.html'
    context_object_name = 'question_bank'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.select_related(
            'question_type', 'hsk_level'
        ).order_by('question_type', 'created_at')
        context['questions_by_type'] = self.object.questions_by_type()
        return context


class QuestionBankCreateView(LoginRequiredMixin, CreateView):
    """Create view for question banks"""
    model = QuestionBank
    form_class = QuestionBankForm
    template_name = 'questions/questionbank_form.html'
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Ngân hàng câu hỏi "{form.instance.name}" đã được tạo!'
        )
        return super().form_valid(form)


class QuestionBankUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for question banks"""
    model = QuestionBank
    form_class = QuestionBankForm
    template_name = 'questions/questionbank_form.html'
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Ngân hàng câu hỏi "{form.instance.name}" đã được cập nhật!'
        )
        return super().form_valid(form)


class QuestionBankDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for question banks"""
    model = QuestionBank
    template_name = 'questions/questionbank_confirm_delete.html'
    success_url = reverse_lazy('questions:banks_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(
            request, 
            f'Ngân hàng câu hỏi "{self.get_object().name}" đã được xóa!'
        )
        return super().delete(request, *args, **kwargs)


# Import Views
@login_required
def import_questions_view(request):
    """View for importing questions from CSV/JSON files"""
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = process_import(form.cleaned_data)
                
                # Display success/error messages
                if result['created'] > 0:
                    messages.success(
                        request, 
                        f'Đã tạo thành công {result["created"]} câu hỏi mới!'
                    )
                
                if result.get('updated', 0) > 0:
                    messages.success(
                        request,
                        f'Đã cập nhật {result["updated"]} câu hỏi!'
                    )
                
                if result["errors"]:
                    for error in result["errors"][:5]:  # Show first 5 errors
                        messages.warning(request, error)
                    
                    if len(result["errors"]) > 5:
                        messages.warning(
                            request,
                            f'Và {len(result["errors"]) - 5} lỗi khác...'
                        )
                
                if result['created'] == 0 and result.get('updated', 0) == 0:
                    messages.info(
                        request,
                        'Không có câu hỏi nào được import. Kiểm tra lại file và cài đặt.'
                    )
                
                return redirect('questions:import')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Lỗi khi import: {str(e)}'
                )
    else:
        form = ImportForm()
    
    return render(request, 'questions/import_questions.html', {
        'form': form
    })


def process_import(cleaned_data):
    """Process import of questions from file using the QuestionImporter"""
    file = cleaned_data['file']
    file_type = cleaned_data['file_type']
    hsk_level = cleaned_data['hsk_level']
    question_bank = cleaned_data.get('question_bank')
    create_new_bank = cleaned_data.get('create_new_bank')
    new_bank_name = cleaned_data.get('new_bank_name')
    overwrite_duplicates = cleaned_data.get('overwrite_duplicates', False)
    
    # Create new question bank if requested
    if create_new_bank and new_bank_name:
        question_bank, created = QuestionBank.objects.get_or_create(
            name=new_bank_name,
            hsk_level=hsk_level,
            defaults={
                'description': f'Imported from {file.name}',
                'is_active': True
            }
        )
    
    # Use the QuestionImporter class
    importer = QuestionImporter()
    result = importer.import_from_file(
        file=file,
        file_type=file_type,
        hsk_level=hsk_level,
        question_bank=question_bank,
        overwrite_duplicates=overwrite_duplicates
    )
    
    return result


# Function-based views for backward compatibility
def question_list_view(request):
    """List all questions"""
    return QuestionListView.as_view()(request)


def question_detail_view(request, question_id):
    """Question detail view"""
    return QuestionDetailView.as_view()(request, pk=question_id)


@login_required
def question_create_view(request):
    """Create new question"""
    context = {}
    return render(request, 'questions/question_form.html', context)

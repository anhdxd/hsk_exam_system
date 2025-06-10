from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    # Question URLs
    path('', views.QuestionListView.as_view(), name='list'),
    path('create/', views.QuestionCreateView.as_view(), name='create'),
    path('<int:pk>/', views.QuestionDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.QuestionUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='delete'),
      # Question Bank URLs
    path('banks/', views.QuestionBankListView.as_view(), name='banks_list'),
    path('banks/create/', views.QuestionBankCreateView.as_view(), name='banks_create'),
    path('banks/<int:pk>/', views.QuestionBankDetailView.as_view(), name='banks_detail'),
    path('banks/<int:pk>/edit/', views.QuestionBankUpdateView.as_view(), name='banks_update'),
    path('banks/<int:pk>/delete/', views.QuestionBankDeleteView.as_view(), name='banks_delete'),
    
    # Import URLs
    path('import/', views.import_questions_view, name='import'),
    
    # Function-based view alternatives (for backward compatibility)
    path('list-func/', views.question_list_view, name='list_func'),
    path('<int:question_id>/detail-func/', views.question_detail_view, name='detail_func'),
]

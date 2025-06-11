from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # Main exam URLs
    path('', views.ExamListView.as_view(), name='list'),
    path('<int:pk>/', views.ExamDetailView.as_view(), name='detail'),
    path('create/', views.ExamCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ExamUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ExamDeleteView.as_view(), name='delete'),
    
    # Exam taking URLs
    path('<int:pk>/start/', views.start_exam_view, name='start'),
    path('session/<int:pk>/take/', views.take_exam_view, name='take_exam'),
    path('session/<int:pk>/continue/', views.continue_exam_view, name='continue_exam'),
    path('session/<int:pk>/result/', views.exam_result_view, name='result'),    # AJAX URLs
    path('session/<int:pk>/time-check/', views.exam_time_check, name='time_check'),
    path('session/<int:pk>/save-answer/', views.save_answer_ajax, name='save_answer_ajax'),
    path('session/<int:pk>/get-question/', views.get_question_ajax, name='get_question_ajax'),
    path('session/<int:pk>/navigate/', views.navigate_question_ajax, name='navigate_question_ajax'),
    path('session/<int:pk>/complete/', views.complete_exam_ajax, name='complete_exam_ajax'),
    
    # Admin URLs
    path('sessions/', views.ExamSessionListView.as_view(), name='session_list'),
]

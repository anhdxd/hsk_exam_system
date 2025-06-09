from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.exam_list_view, name='list'),
    path('<int:exam_id>/', views.exam_detail_view, name='detail'),
    path('<int:exam_id>/start/', views.start_exam_view, name='start'),
    path('session/<int:session_id>/', views.take_exam_view, name='take'),
    path('session/<int:session_id>/result/', views.exam_result_view, name='result'),
]

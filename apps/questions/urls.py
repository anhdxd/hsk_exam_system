from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.question_list_view, name='list'),
    path('create/', views.question_create_view, name='create'),
    path('<int:question_id>/', views.question_detail_view, name='detail'),
    path('import/', views.import_questions_view, name='import'),
]

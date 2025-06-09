from django.urls import path
from . import views

app_name = 'submissions'

urlpatterns = [
    path('', views.submission_list_view, name='list'),
    path('<int:submission_id>/', views.submission_detail_view, name='detail'),
]

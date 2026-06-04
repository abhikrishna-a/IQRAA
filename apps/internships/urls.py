from django.urls import path

from . import views

urlpatterns = [
    path('companies/', views.company_list, name='company-list'),
    path('companies/<int:pk>/', views.company_detail, name='company-detail'),
    path('internships/', views.internship_list, name='internship-list'),
    path('internships/<int:pk>/', views.internship_detail, name='internship-detail'),
]

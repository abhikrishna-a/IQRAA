from django.urls import path

from . import views

urlpatterns = [
    path('applications/', views.application_list, name='application-list'),
    path('applications/<int:pk>/', views.application_detail, name='application-detail'),
]

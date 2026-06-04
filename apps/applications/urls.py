from django.urls import path

from . import views

urlpatterns = [
    path('applications/', views.application_list, name='application-list'),
    path('applications/<int:pk>/', views.application_detail, name='application-detail'),
    path('applications/<int:pk>/status/', views.application_update_status, name='application-status'),
]

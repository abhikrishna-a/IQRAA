from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include(('apps.authentication.urls', 'auth'))),
    path('api/', include(('apps.internships.urls', 'internships'))),
    path('api/', include(('apps.applications.urls', 'applications'))),
]

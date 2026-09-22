from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('expenses.urls')),

    # Interactive API docs - lets a reviewer try every endpoint from the
    # browser without needing Postman.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Minimal frontend (plain HTML/JS) - confirms end-to-end functionality.
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

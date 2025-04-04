# urls.py
from django.urls import path
from .views import analyze_pdf

urlpatterns = [
    path('pdf-risk-analysis/', analyze_pdf, name='analyze_pdf'),
]

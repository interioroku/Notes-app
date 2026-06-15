from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, NoteViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='note')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]

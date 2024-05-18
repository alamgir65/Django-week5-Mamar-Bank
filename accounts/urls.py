
from django.urls import path
from . import views
urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register' ),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logoutUser/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileUpdate.as_view(), name='profile'),
]
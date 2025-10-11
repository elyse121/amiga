from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('votes/', views.index, name='index'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='votes/registration/login.html'
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        template_name='votes/registration/logged_out.html',
        next_page='login'
    ), name='logout'),
    path('votes/get_assignments/', views.get_assignments, name='get_assignments'),
    path('votes/submit_rating/', views.submit_rating, name='submit_rating'),
    path('refresh-assignments/', views.refresh_assignments, name='refresh_assignments'),

]
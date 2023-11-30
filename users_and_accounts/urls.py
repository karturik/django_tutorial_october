from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name="registration/custom_password_reset_form.html",
                                                                 email_template_name="registration/custom_password_reset_email.html"),
         name='password_reset'),
    path('password_reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/custom_password_reset_complete.html'),
         name='password_reset_complete'),
    path('password_reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/custom_password_reset_confirm.html'),
         name='custom_password_reset_confirm'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/custom_password_reset_done.html'),
         name='password_reset_done'),
    # path('profile/', views.profile_view, name='user_profile'),
    # path('', include('django.contrib.auth.urls')),  # Include Django authentication URLs
]
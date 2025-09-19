from django.urls import path
from . import views

urlpatterns = [
    # Registration
    path("register/", views.register, name="register"),

    # Custom login/logout
    path("login/", views.custom_login, name="login"),
    path("logout/", views.custom_logout, name="logout"),

    # Password reset
    path("password_reset/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset_done/", views.CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]

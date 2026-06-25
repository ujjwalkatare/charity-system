from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('donor_register', views.donor_register, name='donor_register'),
    path('trust_register', views.trust_register, name='trust_register'),
    path('log_in', views.log_in, name='log_in'),
    path("logout/", views.user_logout, name="logout"),
    path('user_dashboard', views.user_dashboard, name='user_dashboard'),
    path('donation', views.donation, name='donation'),
    path('show_donation/', views.show_donation, name='show_donation'),
    path('trust_dashboard', views.trust_dashboard, name='trust_dashboard'),
    path('utilize_donation', views.utilize_donation, name='utilize_donation'),
    path('show_utilization', views.show_utilization, name='show_utilization'),
    path('super_admin_dashboard', views.super_admin_dashboard, name='super_admin_dashboard'),
    path(
    "super_admin_transactions",
    views.super_admin_transactions,
    name="super_admin_transactions"),

    path(
    "approve_utilization/<int:utilization_id>/",
    views.approve_utilization,
    name="approve_utilization"),

    path(
    "reject_utilization/<int:utilization_id>/",
    views.reject_utilization,
    name="reject_utilization"),

]
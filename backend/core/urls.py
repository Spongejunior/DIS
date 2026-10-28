"""Page URLs. The Next.js pages live at the same paths and load these through
the JSON bridge (/api/v1/page/<path>). Names match the old Flask endpoints."""
from django.urls import path

from . import views

urlpatterns = [
    path('landing', views.landing_page, name='landing_page'),
    path('set-language', views.set_language, name='set_language'),
    path('', views.index, name='index'),

    path('login', views.login_view, name='login'),
    path('forgot-password', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>', views.reset_password, name='reset_password'),
    path('register', views.register, name='register'),
    path('logout', views.logout_view, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),

    # Farmer
    path('farmer/dashboard', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/notifications', views.farmer_notifications, name='farmer_notifications'),
    path('farmer/notifications/<int:notification_id>', views.farmer_notification_detail,
         name='farmer_notification_detail'),
    path('farmer/notifications/mark-all-read', views.mark_farmer_notifications_read,
         name='mark_farmer_notifications_read'),
    path('farmer/contact-vet', views.contact_vet, name='contact_vet'),
    path('farmer/symptoms', views.symptom_form, name='symptom_form'),
    path('farmer/symptoms/history', views.symptom_history, name='symptom_history'),
    path('farmer/predictions', views.farmer_predictions, name='farmer_predictions'),
    path('farmer/profile', views.farmer_registration, name='farmer_registration'),
    path('predictions/<int:prediction_id>', views.prediction_detail, name='prediction_detail'),
    path('predictions/<int:prediction_id>/pdf', views.prediction_pdf, name='prediction_pdf'),

    # Veterinarian
    path('veterinarian/dashboard', views.vet_dashboard, name='vet_dashboard'),
    path('veterinarian/communications', views.vet_communications, name='vet_communications'),
    path('veterinarian/alerts/send', views.send_farmer_alert, name='send_farmer_alert'),
    path('veterinarian/meetings/schedule', views.schedule_farmer_meeting, name='schedule_farmer_meeting'),
    path('veterinarian/profile', views.vet_profile, name='vet_profile'),
    path('veterinarian/farmers', views.farmer_mapping, name='farmer_mapping'),
    path('veterinarian/predictions', views.predictions_review, name='predictions_review'),
    path('veterinarian/treatments', views.treatment_suggestions, name='treatment_suggestions'),
    path('veterinarian/predictions/<int:prediction_id>/treatment', views.add_treatment, name='add_treatment'),
    path('veterinarian/mortality', views.mortality_reports, name='mortality_reports'),

    # Organization admin
    path('organization/dashboard', views.org_admin_dashboard, name='org_admin_dashboard'),
    path('organization/profile', views.org_admin_profile, name='org_admin_profile'),
    path('organization/user_management', views.org_admin_users, name='org_admin_users'),
    path('organization/users/<int:user_id>/approve', views.approve_user, name='approve_user'),
    path('organization/users/<int:user_id>/reject', views.reject_user, name='reject_user'),
    path('organization/users/<int:user_id>/delete', views.delete_user, name='delete_user'),
    path('organization/reports', views.org_reports, name='org_reports'),
    path('organization/reports/pdf', views.org_reports_pdf, name='org_reports_pdf'),

    # System admin
    path('system/dashboard', views.sys_admin_dashboard, name='sys_admin_dashboard'),
    path('system/logs', views.system_logs, name='system_logs'),
    path('system/performance', views.performance_reports, name='performance_reports'),
    path('system/updates', views.model_updates, name='model_updates'),

    # Actions posted by the veterinarian pages
    path('api/predictions/<int:prediction_id>/review', views.review_prediction, name='review_prediction'),
    path('api/treatments/<int:treatment_id>/approve', views.approve_treatment, name='approve_treatment'),
]

# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('professor/', views.professor_dashboard, name='professor_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('register-student/', views.register_student, name='register_student'),
    path('register-professor/', views.register_professor, name='register_professor'),
    path('register-subject/', views.register_subject, name='register_subject'),
    path('assign-professor/<int:professor_id>/<int:subject_id>/',
         views.assign_professor_to_subject, name='assign_professor_to_subject'),
    path('remove-professor/<int:subject_id>/',
         views.remove_professor_from_subject, name='remove_professor_from_subject'),
    path('notifications/', views.notifications_view, name='notifications'),
path('admin/application-details/<int:notification_id>/', views.application_details, name='application_details'),
]
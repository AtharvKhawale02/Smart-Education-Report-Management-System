from django.contrib import admin
from django.urls import path
from home.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', login_page, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_user, name='logout'),
    path('register_user/', register_user, name='register_user'),

    # Dashboards
    path('principal-dashboard/', principal_dashboard, name='principal_dashboard'),
    path('hod-dashboard/', hod_dashboard, name='hod_dashboard'),
    path('faculty-dashboard/', faculty_dashboard, name='faculty_dashboard'),

    # Department and Member Management
    path('manage_departments/', manage_departments, name='manage_departments'),
    path('manage_members/', manage_members, name='manage_members'),

    # Task Management
    path('assign_task_to_hod/', assign_task_to_hod, name='assign_task_to_hod'),
    path('delegate_task/<int:task_id>/', delegate_task, name='delegate_task'),
    path('view_hod_tasks/', view_hod_tasks, name='view_hod_tasks'),
    path('hod/create_task_for_faculty/', create_task_for_faculty, name='create_task_for_faculty'),
    path('view_faculty_tasks/', view_faculty_tasks, name='view_faculty_tasks'),
    path('update_task/<int:task_id>/', update_task, name='update_task'),

    # Report Management
    path('submit-report/', submit_report, name='submit_report'),
    path('review-reports/', review_reports, name='review_reports'),
    path('report/<int:report_id>/review/', approve_reject_report, name='approve_reject_report'),
    path('generate-annual-report/', generate_annual_report, name='generate_annual_report'),
    path('annual-report/<int:report_id>/submit/', submit_annual_report, name='submit_annual_report'),
    path('department-reports/', view_department_reports, name='view_department_reports'),
    path('report-status/', view_report_status, name='view_report_status'),
    path('track-department-reports/', track_department_reports, name='track_department_reports'),
    path('annual-report/<int:report_id>/review/', review_annual_report, name='review_annual_report'),
    path('report/<int:report_id>/download/', download_converted_report, name='download_converted_report'),
    # Analytics
    path('analytics_dashboard/', analytics_dashboard, name='analytics_dashboard'),

    # Comments
    path('add_comment/<int:report_id>/', add_comment, name='add_comment'),
    path('view_comments/<int:report_id>/', view_comments, name='view_comments'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



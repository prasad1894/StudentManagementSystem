from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('change-password/', views.change_password, name='change_password'),
    path(
        'student-leave/add/',
        views.student_leave_create,
        name='student_leave_create'
    ),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance-app/', views.attendance_app, name='attendance_app'),
    path('daily-attendance/', views.daily_attendance, name='daily_attendance'),
    path('period-attendance/', views.period_attendance, name='period_attendance'),
    path('attendance-history/', views.attendance_history, name='attendance_history'),

    path(
        'student-tasks/<int:pk>/update/',
        views.student_task_update,
        name='student_task_update'
    ),

    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/add/', views.faculty_create, name='faculty_create'),
    path('faculty/<int:pk>/assign-classes/', views.faculty_assign_classes, name='faculty_assign_classes'),
    path('faculty/<int:pk>/toggle-status/', views.faculty_toggle_status, name='faculty_toggle_status'),
    path('faculty/<int:pk>/reset-password/', views.faculty_reset_password, name='faculty_reset_password'),

    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.class_create, name='class_create'),
    path('classes/<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),

    # Public registration disabled.
    # Faculty and Student accounts are created by Admin/Faculty management.
    # path('register/', views.register, name='register'),


    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/import/', views.student_import, name='student_import'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:pk>/activate/', views.student_activate, name='student_activate'),

    path('tasks/', views.task_list, name='task_list'),
    path('tasks/add/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),

    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/add/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StudentAPIViewSet,
    SubjectAPIViewSet,
    AttendanceAPIViewSet,
    TaskAPIViewSet,
    LeaveRequestAPIViewSet,
    save_attendance_app,
    attendance_app_students,
    attendance_app_classes,
)

router = DefaultRouter()

router.register('students', StudentAPIViewSet, basename='api-students')
router.register('subjects', SubjectAPIViewSet, basename='api-subjects')
router.register('attendance', AttendanceAPIViewSet, basename='api-attendance')
router.register('tasks', TaskAPIViewSet, basename='api-tasks')
router.register('leaves', LeaveRequestAPIViewSet, basename='api-leaves')

urlpatterns = [
    path('', include(router.urls)),
    path('attendance-app/save/', save_attendance_app, name='save-attendance-app'),
    path('attendance-app/students/', attendance_app_students, name='attendance-app-students'),
    path('attendance-app/classes/', attendance_app_classes, name='attendance-app-classes'),
]
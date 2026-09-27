from rest_framework import serializers
from .models import Student, Subject, Attendance, Task, LeaveRequest


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id',
            'roll_number',
            'name',
            'email',
            'phone',
            'class_section',
            'admission_year',
            'is_active',
        ]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            'id',
            'code',
            'name',
            'class_section',
            'faculty',
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = [
            'id',
            'student',
            'subject',
            'date',
            'status',
            'marked_by',
        ]
        read_only_fields = ['marked_by']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'class_section',
            'priority',
            'status',
            'due_date',
            'created_at',
        ]


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'student',
            'leave_type',
            'start_date',
            'end_date',
            'reason',
            'status',
            'applied_at',
        ]
        read_only_fields = ['status', 'applied_at']
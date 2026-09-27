from django.contrib import admin
from .models import (
    Department,
    Employee,
    Task,
    LeaveRequest,
    UserProfile,
    ClassSection,
    Student,
    Attendance,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'created_at',
    )

    search_fields = (
        'name',
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id',
        'name',
        'email',
        'department',
        'designation',
        'is_active',
    )

    search_fields = (
        'employee_id',
        'name',
        'email',
    )

    list_filter = (
        'department',
        'designation',
        'is_active',
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'class_section',
        'priority',
        'status',
        'due_date',
        'created_at',
    )

    search_fields = (
        'title',
        'class_section__branch',
        'class_section__section',
    )

    list_filter = (
        'class_section',
        'priority',
        'status',
        'due_date',
    )

    ordering = ('-created_at',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'leave_type',
        'start_date',
        'end_date',
        'status',
        'applied_at',
    )

    search_fields = (
        'student__name',
        'student__roll_number',
        'reason',
    )

    list_filter = (
        'leave_type',
        'status',
        'start_date',
        'end_date',
    )

    ordering = (
        '-applied_at',
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = (
        'roll_number',
        'name',
        'email',
        'phone',
        'admission_year',
        'is_active',
    )
    readonly_fields = (
        'roll_number',
        'name',
        'email',
        'phone',
        'admission_year',
        'is_active',
    )


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = (
        'year',
        'branch',
        'section',
        'display_faculty',
        'created_at',
    )

    list_filter = (
        'year',
        'branch',
        'section',
    )

    search_fields = (
        'branch',
        'section',
        'faculty__user__username',
    )

    filter_horizontal = ('faculty',)

    inlines = [StudentInline]

    def display_faculty(self, obj):
        return ", ".join(
            profile.user.username
            for profile in obj.faculty.all()
        ) or "-"

    display_faculty.short_description = "Faculty"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'roll_number',
        'name',
        'email',
        'user',
        'class_section',
        'admission_year',
        'is_active',
    )
    search_fields = (
        'roll_number',
        'name',
        'email',
    )
    list_filter = (
        'class_section',
        'is_active',
        'admission_year',
    )
    ordering = ('roll_number',)



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'date',
        'status',
        'marked_by',
        'created_at',
    )

    search_fields = (
        'student__name',
        'student__roll_number',
    )

    list_filter = (
        'status',
        'date',
    )

    ordering = (
        '-date',
        'student__roll_number',
    )
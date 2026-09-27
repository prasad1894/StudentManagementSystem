import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from .models import (
    Employee,
    Task,
    LeaveRequest,
    Department,
    Student,
    ClassSection,
    Attendance,
    UserProfile,
    Subject,
)
from .forms import EmployeeForm, TaskForm, LeaveRequestForm, RegistrationForm, StudentForm, SubjectForm, ClassSectionForm
from django.db import models
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime



def is_admin(user):
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role == 'ADMIN'
    )

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            if hasattr(user, 'profile'):
                if user.profile.must_change_password:
                    return redirect('change_password')

            if (
                hasattr(user, 'profile')
                and user.profile.role == 'STUDENT'
            ):
                return redirect('student_dashboard')

            return redirect('dashboard')

        error = 'Invalid username or password.'

    return render(
        request,
        'employees/login.html',
        {'error': error}
    )


@login_required
def dashboard(request):

    if (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'STUDENT'
    ):
        return redirect('student_dashboard')

    if is_admin(request.user):
        total_students = Student.objects.filter(is_active=True).count()

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        total_students = Student.objects.filter(
            class_section__faculty=request.user.profile,
            is_active=True
        ).count()

    else:
        total_students = 0

    if is_admin(request.user):
        total_tasks = Task.objects.count()

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        total_tasks = Task.objects.filter(
            class_section__faculty=request.user.profile
        ).count()

    else:
        total_tasks = 0

    if is_admin(request.user):
        pending_leaves = LeaveRequest.objects.filter(
            status='PENDING'
        ).count()

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        pending_leaves = LeaveRequest.objects.filter(
            student__class_section__faculty=request.user.profile,
            status='PENDING'
        ).count()

    else:
        pending_leaves = 0

    if is_admin(request.user):
        completed_tasks = Task.objects.filter(
            status='COMPLETED'
        ).count()

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        completed_tasks = Task.objects.filter(
            class_section__faculty=request.user.profile,
            status='COMPLETED'
        ).count()

    else:
        completed_tasks = 0

    if is_admin(request.user):
        recent_tasks = Task.objects.select_related(
            'class_section'
        ).order_by('-created_at')[:5]

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        recent_tasks = Task.objects.filter(
            class_section__faculty=request.user.profile
        ).select_related(
            'class_section'
        ).order_by('-created_at')[:5]

    else:
        recent_tasks = Task.objects.none()

    if is_admin(request.user):
        recent_leaves = LeaveRequest.objects.select_related(
            'student',
            'student__class_section'
        ).order_by('-applied_at')[:5]

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        recent_leaves = LeaveRequest.objects.filter(
            student__class_section__faculty=request.user.profile
        ).select_related(
            'student',
            'student__class_section'
        ).order_by('-applied_at')[:5]

    else:
        recent_leaves = LeaveRequest.objects.none()

    if is_admin(request.user):
        assigned_classes = ClassSection.objects.all()
    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        assigned_classes = request.user.profile.assigned_classes.all()
    else:
        assigned_classes = ClassSection.objects.none()



    if is_admin(request.user):
        attendance_records = Attendance.objects.all()

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        attendance_records = Attendance.objects.filter(
            student__class_section__faculty=request.user.profile
        )

    else:
        attendance_records = Attendance.objects.none()

    total_attendance = attendance_records.count()

    present_count = attendance_records.filter(
        status='PRESENT'
    ).count()

    absent_count = attendance_records.filter(
        status='ABSENT'
    ).count()

    attendance_percentage = (
        (present_count / total_attendance) * 100
        if total_attendance > 0 else 0
    )

    recent_attendance = attendance_records.select_related(
        'student',
        'student__class_section',
        'subject'
    ).order_by('-date', 'student__roll_number')[:10]



    context = {
        'total_students': total_students,
        'total_tasks': total_tasks,
        'pending_leaves': pending_leaves,
        'completed_tasks': completed_tasks,
        'recent_tasks': recent_tasks,
        'recent_leaves': recent_leaves,
        'assigned_classes': assigned_classes,
        'total_attendance': total_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'recent_attendance': recent_attendance,
    }

    return render(
        request,
        'employees/dashboard.html',
        context
    )


@login_required
@user_passes_test(is_admin)
def employee_list(request):
    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', '').strip()

    employees = Employee.objects.select_related(
        'department'
    ).order_by('name')

    if search:
        employees = employees.filter(
            models.Q(employee_id__icontains=search) |
            models.Q(name__icontains=search) |
            models.Q(email__icontains=search)
        )

    if department:
        employees = employees.filter(
            department__name=department
        )

    context = {
        'employees': employees,
        'search': search,
        'department': department,
        'departments': Department.objects.all().order_by('name'),
    }

    return render(
        request,
        'employees/employee_list.html',
        context
    )


@login_required
@user_passes_test(is_admin)
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('employee_list')

    else:
        form = EmployeeForm()

    return render(
        request,
        'employees/employee_form.html',
        {'form': form}
    )


@login_required
@user_passes_test(is_admin)
def employee_edit(request, pk):
    employee = Employee.objects.get(pk=pk)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)

        if form.is_valid():
            form.save()
            return redirect('employee_list')

    else:
        form = EmployeeForm(instance=employee)

    return render(
        request,
        'employees/employee_form.html',
        {
            'form': form,
            'employee': employee,
        }
    )


@login_required
@user_passes_test(is_admin)
def employee_delete(request, pk):
    employee = Employee.objects.get(pk=pk)

    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')

    return render(
        request,
        'employees/employee_confirm_delete.html',
        {
            'employee': employee,
        }
    )


@login_required
def task_list(request):
    if is_admin(request.user):
        tasks = Task.objects.select_related(
            'class_section'
        ).order_by('-created_at')

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        tasks = Task.objects.filter(
            class_section__faculty=request.user.profile
        ).select_related(
            'class_section'
        ).order_by('-created_at')

    else:
        return redirect('dashboard')

    context = {
        'tasks': tasks,
    }

    return render(
        request,
        'employees/task_list.html',
        context
    )


@login_required
def task_create(request):

    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    if request.method == 'POST':
        form = TaskForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            task = form.save()

            # Faculty can create tasks only
            # for their assigned class sections.
            if (
                request.user.profile.role == 'FACULTY'
                and task.class_section not in
                request.user.profile.assigned_classes.all()
            ):
                task.delete()
                return redirect('task_list')

            return redirect('task_list')

    else:
        form = TaskForm(
            user=request.user
        )

    return render(
        request,
        'employees/task_form.html',
        {'form': form}
    )


@login_required
def task_edit(request, pk):
    task = get_object_or_404(
        Task.objects.select_related('class_section'),
        pk=pk
    )

    if is_admin(request.user):
        pass

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if task.class_section not in request.user.profile.assigned_classes.all():
            return redirect('task_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        form = TaskForm(
            request.POST,
            instance=task,
            user=request.user
        )

        if form.is_valid():
            form.save()
            return redirect('task_list')

    else:
        form = TaskForm(
            instance=task,
            user=request.user
        )

    return render(
        request,
        'employees/task_form.html',
        {
            'form': form,
            'task': task,
        }
    )


@login_required
def task_delete(request, pk):
    task = get_object_or_404(
        Task.objects.select_related('class_section'),
        pk=pk
    )

    if is_admin(request.user):
        pass

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if task.class_section not in request.user.profile.assigned_classes.all():
            return redirect('task_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        task.delete()
        return redirect('task_list')

    return render(
        request,
        'employees/task_confirm_delete.html',
        {
            'task': task,
        }
    )


@login_required
def leave_create(request):

    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    if request.method == 'POST':
        form = LeaveRequestForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            leave = form.save()

            # Faculty can create leave requests only
            # for students in their assigned classes.
            if (
                request.user.profile.role == 'FACULTY'
                and leave.student.class_section not in
                request.user.profile.assigned_classes.all()
            ):
                leave.delete()
                return redirect('leave_list')

            return redirect('leave_list')

    else:
        form = LeaveRequestForm(
            user=request.user
        )

    return render(
        request,
        'employees/leave_form.html',
        {'form': form}
    )


@login_required
def leave_list(request):

    if is_admin(request.user):
        leaves = LeaveRequest.objects.select_related(
            'student',
            'student__class_section'
        ).order_by('-applied_at')

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        leaves = LeaveRequest.objects.filter(
            student__class_section__faculty=request.user.profile
        ).select_related(
            'student',
            'student__class_section'
        ).order_by('-applied_at')

    else:
        return redirect('dashboard')

    context = {
        'leaves': leaves,
    }

    return render(
        request,
        'employees/leave_list.html',
        context
    )


@login_required
def leave_approve(request, pk):

    leave = get_object_or_404(
        LeaveRequest.objects.select_related(
            'student',
            'student__class_section'
        ),
        pk=pk
    )

    if is_admin(request.user):
        pass

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if leave.student.class_section not in request.user.profile.assigned_classes.all():
            return redirect('leave_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        leave.status = 'APPROVED'
        leave.save()
        return redirect('leave_list')

    return redirect('leave_list')


@login_required
def leave_reject(request, pk):

    leave = get_object_or_404(
        LeaveRequest.objects.select_related(
            'student',
            'student__class_section'
        ),
        pk=pk
    )

    if is_admin(request.user):
        pass

    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if leave.student.class_section not in request.user.profile.assigned_classes.all():
            return redirect('leave_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        leave.status = 'REJECTED'
        leave.save()
        return redirect('leave_list')

    return redirect('leave_list')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(
        request,
        'employees/register.html',
        {'form': form}
    )


@login_required
def student_list(request):

    if is_admin(request.user):
        students = Student.objects.select_related(
            'class_section'
        ).order_by('roll_number')

    elif (
        request.user.is_authenticated
        and hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        students = Student.objects.filter(
            class_section__faculty=request.user.profile
        ).select_related(
            'class_section'
        ).order_by('roll_number')

    else:
        students = Student.objects.none()

    return render(
        request,
        'employees/student_list.html',
        {'students': students}
    )


@login_required
def student_create(request):
    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():

            student = form.save(commit=False)

            roll_number = student.roll_number

            if User.objects.filter(
                username=roll_number
            ).exists():
                form.add_error(
                    'roll_number',
                    'A login account already exists for this roll number.'
                )

            else:
                student.save()

                user = User.objects.create_user(
                    username=roll_number,
                    email=student.email,
                    password=roll_number
                )

                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'STUDENT',
                        'must_change_password': True,
                    }
                )

                if not created:
                    profile.role = 'STUDENT'
                    profile.must_change_password = True
                    profile.save(
                        update_fields=['role', 'must_change_password']
                    )

                student.user = user
                student.save(update_fields=['user'])

                return redirect('student_list')

    else:
        form = StudentForm(user=request.user)

    return render(
        request,
        'employees/student_form.html',
        {'form': form}
    )


@login_required
def student_import(request):
    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    error = None
    success_count = 0
    skipped_count = 0

    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            error = 'Please select a CSV file.'

        elif not csv_file.name.endswith('.csv'):
            error = 'Please upload a CSV file.'

        else:
            try:
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)

                required_columns = {
                    'roll_number',
                    'name',
                    'email',
                    'phone',
                    'class_section',
                    'admission_year',
                }

                if not required_columns.issubset(reader.fieldnames or []):
                    error = (
                        'CSV must contain: '
                        'roll_number, name, email, phone, '
                        'class_section, admission_year'
                    )
                else:
                    for row in reader:

                        roll_number = row['roll_number'].strip()
                        name = row['name'].strip()
                        email = row['email'].strip()
                        phone = row['phone'].strip()
                        class_name = row['class_section'].strip()
                        admission_year = row['admission_year'].strip()

                        class_section = ClassSection.objects.filter(
                            year__in=['1', '2', '3', '4']
                        )

                        selected_class = None

                        for cls in class_section:
                            if str(cls) == class_name:
                                selected_class = cls
                                break

                        if not selected_class:
                            skipped_count += 1
                            continue

                        if Student.objects.filter(
                            roll_number=roll_number
                        ).exists():
                            skipped_count += 1
                            continue

                        if User.objects.filter(
                            username=roll_number
                        ).exists():
                            skipped_count += 1
                            continue

                        if (
                            request.user.profile.role == 'FACULTY'
                            and not selected_class.faculty.filter(
                                id=request.user.profile.id
                            ).exists()
                        ):
                            skipped_count += 1
                            continue

                        student = Student.objects.create(
                            roll_number=roll_number,
                            name=name,
                            email=email,
                            phone=phone,
                            class_section=selected_class,
                            admission_year=int(admission_year),
                            is_active=True,
                        )

                        user = User.objects.create_user(
                            username=roll_number,
                            email=email,
                            password=roll_number
                        )

                        profile, created = UserProfile.objects.get_or_create(
                            user=user,
                            defaults={
                                'role': 'STUDENT',
                                'must_change_password': True,
                            }
                        )

                        if not created:
                            profile.role = 'STUDENT'
                            profile.must_change_password = True
                            profile.save(update_fields=['role', 'must_change_password'])

                        student.user = user
                        student.save(update_fields=['user'])

                        success_count += 1

            except Exception as e:
                error = f'Import failed: {e}'

    return render(
        request,
        'employees/student_import.html',
        {
            'error': error,
            'success_count': success_count,
            'skipped_count': skipped_count,
        }
    )


@login_required
def student_edit(request, pk):

    student = get_object_or_404(
        Student.objects.select_related('class_section'),
        pk=pk
    )

    # Admin can edit any student.
    if is_admin(request.user):
        pass

    # Faculty can edit only students
    # from their assigned classes.
    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if student.class_section not in request.user.profile.assigned_classes.all():
            return redirect('student_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentForm(
            request.POST,
            instance=student,
            user=request.user
        )

        if form.is_valid():
            form.save()
            return redirect('student_list')

    else:
        form = StudentForm(
            instance=student,
            user=request.user
        )

    return render(
        request,
        'employees/student_form.html',
        {
            'form': form,
            'student': student,
        }
    )


@login_required
def student_delete(request, pk):

    student = get_object_or_404(
        Student.objects.select_related('class_section'),
        pk=pk
    )

    # Admin can deactivate any student.
    if is_admin(request.user):
        pass

    # Faculty can deactivate only students
    # from their assigned classes.
    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if student.class_section not in request.user.profile.assigned_classes.all():
            return redirect('student_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        student.is_active = False
        student.save(update_fields=['is_active'])
        return redirect('student_list')

    return render(
        request,
        'employees/student_confirm_delete.html',
        {'student': student}
    )




@login_required
def student_activate(request, pk):

    student = get_object_or_404(
        Student.objects.select_related('class_section'),
        pk=pk
    )

    # Admin can activate any student.
    if is_admin(request.user):
        pass

    # Faculty can activate only students
    # from their assigned classes.
    elif (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        if student.class_section not in request.user.profile.assigned_classes.all():
            return redirect('student_list')

    else:
        return redirect('dashboard')

    if request.method == 'POST':
        student.is_active = True
        student.save(update_fields=['is_active'])
        return redirect('student_list')

    return render(
        request,
        'employees/student_confirm_activate.html',
        {'student': student}
    )



@login_required
def student_dashboard(request):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'STUDENT'
        and hasattr(request.user, 'student_profile')
    ):
        return redirect('dashboard')

    student = request.user.student_profile

    tasks = Task.objects.filter(
        class_section=student.class_section
    ).order_by('due_date')

    leaves = LeaveRequest.objects.filter(
        student=student
    ).order_by('-applied_at')

    attendance_records = Attendance.objects.filter(
        student=student
    ).order_by('-date')

    total_attendance = attendance_records.count()
    present_count = attendance_records.filter(status='PRESENT').count()
    absent_count = attendance_records.filter(status='ABSENT').count()

    attendance_percentage = (
        (present_count / total_attendance) * 100
        if total_attendance > 0 else 0
    )

    context = {
        'student': student,
        'tasks': tasks,
        'leaves': leaves,
        'attendance_records': attendance_records,
        'total_attendance': total_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
    }

    return render(
        request,
        'employees/student_dashboard.html',
        context
    )


@login_required
def student_leave_create(request):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'STUDENT'
        and hasattr(request.user, 'student_profile')
    ):
        return redirect('dashboard')

    student = request.user.student_profile

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        form.fields.pop('student', None)

        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = student
            leave.status = 'PENDING'
            leave.save()

            return redirect('student_dashboard')

    else:
        form = LeaveRequestForm()
        form.fields.pop('student', None)

    return render(
        request,
        'employees/student_leave_form.html',
        {'form': form}
    )



@login_required
def attendance(request):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        return redirect('dashboard')

    assigned_classes = request.user.profile.assigned_classes.all()

    if request.method == 'POST':

        class_id = request.POST.get('class_id')
        subject_id = request.POST.get('subject_id')
        attendance_date = request.POST.get('attendance_date')

        selected_class = assigned_classes.filter(
            id=class_id
        ).first()

        if not selected_class:
            return redirect('attendance')

        selected_subject = Subject.objects.filter(
            id=subject_id,
            class_section=selected_class
        ).first()

        if not selected_subject:
            return redirect('attendance')

        students = Student.objects.filter(
            class_section=selected_class,
            is_active=True
        ).order_by('roll_number')

        for student in students:

            status = request.POST.get(
                f'attendance_{student.id}'
            )

            if status in ['PRESENT', 'ABSENT']:

                Attendance.objects.update_or_create(
                    student=student,
                    subject=selected_subject,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                    }
                )

        return redirect(
            f'/attendance/?class_id={selected_class.id}'
            f'&subject_id={selected_subject.id}'
            f'&date={attendance_date}'
        )

    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')
    attendance_date = request.GET.get('date')

    if not attendance_date:
        from datetime import date
        attendance_date = date.today().isoformat()

    students = Student.objects.none()
    selected_class = None
    selected_subject = None

    total_students = 0
    present_count = 0
    absent_count = 0
    attendance_percentage = 0

    subjects = Subject.objects.none()

    if selected_class_id:

        selected_class = assigned_classes.filter(
            id=selected_class_id
        ).first()

        if selected_class:

            subjects = Subject.objects.filter(
                class_section=selected_class
            ).order_by('code')

            if selected_subject_id:

                selected_subject = subjects.filter(
                    id=selected_subject_id
                ).first()

            students = Student.objects.filter(
                class_section=selected_class,
                is_active=True
            ).order_by('roll_number')

            total_students = students.count()

            if selected_subject and attendance_date:

                present_count = Attendance.objects.filter(
                    student__in=students,
                    subject=selected_subject,
                    date=attendance_date,
                    status='PRESENT'
                ).count()

                absent_count = Attendance.objects.filter(
                    student__in=students,
                    subject=selected_subject,
                    date=attendance_date,
                    status='ABSENT'
                ).count()

                marked_count = present_count + absent_count

                attendance_percentage = (
                    (present_count / marked_count) * 100
                    if marked_count > 0 else 0
                )

                attendance_records = {}

                records = Attendance.objects.filter(
                    student__in=students,
                    subject=selected_subject,
                    date=attendance_date
                )

                attendance_records = {
                    record.student_id: record.status
                    for record in records
                }

                for student in students:

                    student.attendance_status = (
                        attendance_records.get(
                            student.id,
                            'PRESENT'
                        )
                    )

    context = {
        'assigned_classes': assigned_classes,
        'subjects': subjects,
        'students': students,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'attendance_date': attendance_date,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
    }

    return render(
        request,
        'employees/attendance.html',
        context
    )



@login_required
def student_task_update(request, pk):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'STUDENT'
        and hasattr(request.user, 'student_profile')
    ):
        return redirect('dashboard')

    student = request.user.student_profile

    task = Task.objects.filter(
        pk=pk,
        class_section=student.class_section
    ).first()

    if not task:
        return redirect('student_dashboard')

    if request.method == 'POST':
        status = request.POST.get('status')

        if status in ['TODO', 'IN_PROGRESS', 'COMPLETED']:
            task.status = status
            task.save(update_fields=['status'])

    return redirect('student_dashboard')


@login_required
def faculty_list(request):
    if not is_admin(request.user):
        return redirect('dashboard')

    faculty_profiles = UserProfile.objects.filter(
        role='FACULTY'
    ).select_related('user').order_by('user__username')

    return render(
        request,
        'employees/faculty_list.html',
        {'faculty_profiles': faculty_profiles}
    )


@login_required
def faculty_create(request):
    if not is_admin(request.user):
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            return render(
                request,
                'employees/faculty_form.html',
                {
                    'error': 'Username already exists.',
                    'username': username,
                    'email': email
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password='staff@123'
        )

        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'FACULTY',
                'must_change_password': True
            }
        )

        if not created:
            profile.role = 'FACULTY'
            profile.must_change_password = True
            profile.save(update_fields=['role', 'must_change_password'])

        return redirect('faculty_list')

    return render(request, 'employees/faculty_form.html')


@login_required
def change_password(request):
    if request.method == 'POST':

        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if not password or not password_confirm:
            return render(
                request,
                'employees/change_password.html',
                {'error': 'Please enter both passwords.'}
            )

        if password != password_confirm:
            return render(
                request,
                'employees/change_password.html',
                {'error': 'Passwords do not match.'}
            )

        if len(password) < 8:
            return render(
                request,
                'employees/change_password.html',
                {'error': 'Password must be at least 8 characters.'}
            )

        request.user.set_password(password)
        request.user.save()

        if hasattr(request.user, 'profile'):
            request.user.profile.must_change_password = False
            request.user.profile.save(
                update_fields=['must_change_password']
            )

        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)

        if (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'STUDENT'
        ):
            return redirect('student_dashboard')

        return redirect('dashboard')

    return render(
        request,
        'employees/change_password.html'
    )



@login_required
def faculty_assign_classes(request, pk):
    if not is_admin(request.user):
        return redirect('dashboard')

    faculty_profile = get_object_or_404(
        UserProfile,
        pk=pk,
        role='FACULTY'
    )

    classes = ClassSection.objects.all()

    if request.method == 'POST':
        selected_classes = request.POST.getlist('classes')

        faculty_profile.assigned_classes.set(
            ClassSection.objects.filter(id__in=selected_classes)
        )

        return redirect('faculty_list')

    assigned_classes = faculty_profile.assigned_classes.all()

    return render(
        request,
        'employees/faculty_assign_classes.html',
        {
            'faculty': faculty_profile,
            'classes': classes,
            'assigned_classes': assigned_classes,
        }
    )


@login_required
def faculty_toggle_status(request, pk):
    if not is_admin(request.user):
        return redirect('dashboard')

    profile = get_object_or_404(
        UserProfile,
        pk=pk,
        role='FACULTY'
    )

    profile.user.is_active = not profile.user.is_active
    profile.user.save(update_fields=['is_active'])

    return redirect('faculty_list')


@login_required
def faculty_reset_password(request, pk):
    if not is_admin(request.user):
        return redirect('dashboard')

    profile = get_object_or_404(
        UserProfile,
        pk=pk,
        role='FACULTY'
    )

    profile.user.set_password('staff@123')
    profile.user.save(update_fields=['password'])

    profile.must_change_password = True
    profile.save(update_fields=['must_change_password'])

    return redirect('faculty_list')



@login_required
def subject_list(request):
    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    if request.user.profile.role == 'FACULTY':
        subjects = Subject.objects.filter(
            class_section__faculty=request.user.profile
        ).select_related(
            'class_section',
            'faculty__user'
        )
    else:
        subjects = Subject.objects.select_related(
            'class_section',
            'faculty__user'
        )

    return render(
        request,
        'employees/subject_list.html',
        {'subjects': subjects}
    )


@login_required
def subject_create(request):
    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    if request.method == 'POST':
        form = SubjectForm(request.POST, user=request.user)

        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(user=request.user)

    return render(
        request,
        'employees/subject_form.html',
        {'form': form}
    )



from .serializers import (
    StudentSerializer,
    SubjectSerializer,
    AttendanceSerializer,
    TaskSerializer,
    LeaveRequestSerializer,
)


class StudentAPIViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, 'profile'):
            return Student.objects.none()

        if user.profile.role == 'ADMIN':
            return Student.objects.all().order_by('roll_number')

        if user.profile.role == 'FACULTY':
            return Student.objects.filter(
                class_section__faculty=user.profile
            ).order_by('roll_number')

        if user.profile.role == 'STUDENT':
            if hasattr(user, 'student_profile'):
                return Student.objects.filter(
                    id=user.student_profile.id
                )

        return Student.objects.none()


class SubjectAPIViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, 'profile'):
            return Subject.objects.none()

        if user.profile.role == 'ADMIN':
            return Subject.objects.all().order_by('code')

        if user.profile.role == 'FACULTY':
            return Subject.objects.filter(
                class_section__faculty=user.profile
            ).order_by('code')

        if user.profile.role == 'STUDENT':
            if hasattr(user, 'student_profile'):
                return Subject.objects.filter(
                    class_section=user.student_profile.class_section
                ).order_by('code')

        return Subject.objects.none()


class AttendanceAPIViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, 'profile'):
            return Attendance.objects.none()

        if user.profile.role == 'ADMIN':
            return Attendance.objects.all().select_related(
                'student',
                'subject',
                'marked_by'
            )

        if user.profile.role == 'FACULTY':
            return Attendance.objects.filter(
                student__class_section__faculty=user.profile
            ).select_related(
                'student',
                'subject',
                'marked_by'
            )

        if user.profile.role == 'STUDENT':
            if hasattr(user, 'student_profile'):
                return Attendance.objects.filter(
                    student=user.student_profile
                ).select_related(
                    'student',
                    'subject',
                    'marked_by'
                )

        return Attendance.objects.none()

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)


class TaskAPIViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]


class LeaveRequestAPIViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all().order_by('-applied_at')
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]



@login_required
def subject_edit(request, pk):
    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    subject = get_object_or_404(Subject, pk=pk)

    # Faculty can edit only subjects belonging to their assigned classes
    if (
        request.user.profile.role == 'FACULTY'
        and not subject.class_section.faculty.filter(
            id=request.user.profile.id
        ).exists()
    ):
        return redirect('subject_list')

    if request.method == 'POST':
        form = SubjectForm(
            request.POST,
            instance=subject,
            user=request.user
        )

        if form.is_valid():
            form.save()
            return redirect('subject_list')

    else:
        form = SubjectForm(
            instance=subject,
            user=request.user
        )

    return render(
        request,
        'employees/subject_form.html',
        {
            'form': form,
            'title': 'Edit Subject'
        }
    )




@login_required
def subject_delete(request, pk):
    if not (
        is_admin(request.user)
        or (
            hasattr(request.user, 'profile')
            and request.user.profile.role == 'FACULTY'
        )
    ):
        return redirect('dashboard')

    subject = get_object_or_404(Subject, pk=pk)

    # Faculty can delete only subjects belonging to their assigned classes
    if (
        request.user.profile.role == 'FACULTY'
        and not subject.class_section.faculty.filter(
            id=request.user.profile.id
        ).exists()
    ):
        return redirect('subject_list')

    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')

    return render(
        request,
        'employees/subject_confirm_delete.html',
        {
            'subject': subject
        }
    )



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_attendance_app(request):

    data = request.data

    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    attendance_date = data.get('date')
    present_roll_numbers = data.get('present_roll_numbers', [])
    absent_roll_numbers = data.get('absent_roll_numbers', [])

    # Class and date are always required.
    # Subject is optional because Overall Day Attendance does not use a subject.
    if not class_id or not attendance_date:
        return Response(
            {'error': 'Class and date are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user

    if not hasattr(user, 'profile'):
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Check class permission
    if user.profile.role == 'FACULTY':

        selected_class = user.profile.assigned_classes.filter(
            id=class_id
        ).first()

    elif user.profile.role == 'ADMIN':

        selected_class = ClassSection.objects.filter(
            id=class_id
        ).first()

    else:

        return Response(
            {'error': 'You are not allowed to mark attendance.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if not selected_class:
        return Response(
            {'error': 'Invalid class or you are not assigned to this class.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Subject is optional.
    selected_subject = None

    if subject_id:

        selected_subject = Subject.objects.filter(
            id=subject_id,
            class_section=selected_class
        ).first()

        if not selected_subject:
            return Response(
                {'error': 'Invalid subject for the selected class.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Validate date
    try:

        attendance_date = datetime.strptime(
            attendance_date,
            '%Y-%m-%d'
        ).date()

    except ValueError:

        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get active students from the selected class
    students = Student.objects.filter(
        class_section=selected_class,
        is_active=True
    )

    saved_count = 0

    for student in students:

        if student.roll_number in present_roll_numbers:

            student_status = 'PRESENT'

        elif student.roll_number in absent_roll_numbers:

            student_status = 'ABSENT'

        else:

            continue

        # Find existing attendance record.
        # This works for both:
        # 1. Overall Day Attendance (subject=None)
        # 2. Period-wise Attendance (subject selected)

        attendance_record = Attendance.objects.filter(
            student=student,
            date=attendance_date,
            subject=selected_subject
        ).first()

        if attendance_record:

            attendance_record.status = student_status
            attendance_record.marked_by = request.user
            attendance_record.save()

        else:

            Attendance.objects.create(
                student=student,
                subject=selected_subject,
                date=attendance_date,
                status=student_status,
                marked_by=request.user
            )

        saved_count += 1

    # Prepare response
    if selected_subject:

        attendance_type = 'Period-wise'
        subject_name = selected_subject.code

    else:

        attendance_type = 'Overall Day'
        subject_name = None

    return Response({
        'message': 'Attendance saved successfully.',
        'attendance_type': attendance_type,
        'class': str(selected_class),
        'subject': subject_name,
        'date': str(attendance_date),
        'saved_records': saved_count,
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_app_students(request):

    class_id = request.GET.get('class_id')

    if not class_id:
        return Response(
            {'error': 'class_id is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user

    if not hasattr(user, 'profile'):
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if user.profile.role == 'FACULTY':

        allowed_class = user.profile.assigned_classes.filter(
            id=class_id
        ).first()

        if not allowed_class:
            return Response(
                {'error': 'You are not assigned to this class.'},
                status=status.HTTP_403_FORBIDDEN
            )

    elif user.profile.role == 'ADMIN':

        allowed_class = ClassSection.objects.filter(
            id=class_id
        ).first()

    else:

        return Response(
            {'error': 'You are not allowed to access this data.'},
            status=status.HTTP_403_FORBIDDEN
        )

    students = Student.objects.filter(
        class_section=allowed_class,
        is_active=True
    ).order_by('roll_number')

    data = [
        {
            'id': student.id,
            'roll': student.roll_number,
            'name': student.name,
        }
        for student in students
    ]

    return Response({
        'students': data,
        'total': len(data),
    })




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_app_classes(request):

    user = request.user

    if not hasattr(user, 'profile'):
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if user.profile.role == 'ADMIN':

        classes = ClassSection.objects.all().order_by(
            'year',
            'branch',
            'section'
        )

    elif user.profile.role == 'FACULTY':

        classes = user.profile.assigned_classes.all().order_by(
            'year',
            'branch',
            'section'
        )

    else:

        return Response(
            {'error': 'You are not allowed to access classes.'},
            status=status.HTTP_403_FORBIDDEN
        )

    data = []

    for class_section in classes:

        subjects = Subject.objects.filter(
            class_section=class_section
        ).order_by('code')

        data.append({
            'id': class_section.id,
            'name': (
                f"{class_section.get_year_display()} "
                f"{class_section.branch} - "
                f"{class_section.section} Sec"
            ),
            'subjects': [
                {
                    'id': subject.id,
                    'code': subject.code,
                    'name': subject.name,
                }
                for subject in subjects
            ]
        })

    return Response({
        'classes': data
    })



@login_required
def attendance_app(request):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        return redirect('dashboard')

    return render(
        request,
        'employees/attendance_app.html'
    )




@login_required
def attendance_history(request):

    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        return redirect('dashboard')

    assigned_classes = request.user.profile.assigned_classes.all()

    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')
    selected_date = request.GET.get('date')

    records = Attendance.objects.filter(
        student__class_section__in=assigned_classes
    ).select_related(
        'student',
        'student__class_section',
        'subject'
    ).order_by(
        '-date',
        'student__roll_number'
    )

    if selected_class_id:
        records = records.filter(
            student__class_section_id=selected_class_id
        )

    if selected_subject_id:
        records = records.filter(
            subject_id=selected_subject_id
        )

    if selected_date:
        records = records.filter(
            date=selected_date
        )

    total_records = records.count()

    present_count = records.filter(
        status='PRESENT'
    ).count()

    absent_count = records.filter(
        status='ABSENT'
    ).count()

    attendance_percentage = (
        (present_count / total_records) * 100
        if total_records > 0 else 0
    )

    subjects = Subject.objects.filter(
        class_section__in=assigned_classes
    ).order_by('code')


    # Overall daily attendance summary
    daily_summary = []

    daily_records = records.filter(
        subject__isnull=True
    )

    daily_dates = daily_records.values_list(
        'date',
        flat=True
    ).distinct().order_by('-date')

    for attendance_date in daily_dates:

        date_records = daily_records.filter(
            date=attendance_date
        )

        # Get unique students for this day
        student_status = {}

        for record in date_records:
            student_id = record.student_id

            # If a student has multiple subject records,
            # keep one status for the daily summary.
            if student_id not in student_status:
                student_status[student_id] = record.status

        total_students_day = len(student_status)

        present_day = sum(
            1 for status in student_status.values()
            if status == 'PRESENT'
        )

        absent_day = sum(
            1 for status in student_status.values()
            if status == 'ABSENT'
        )

        percentage_day = (
            (present_day / total_students_day) * 100
            if total_students_day > 0 else 0
        )

        daily_summary.append({
            'date': attendance_date,
            'total_students': total_students_day,
            'present': present_day,
            'absent': absent_day,
            'percentage': percentage_day,
        })


    context = {
        'records': records,
        'assigned_classes': assigned_classes,
        'subjects': subjects,
        'selected_class_id': selected_class_id,
        'selected_subject_id': selected_subject_id,
        'selected_date': selected_date,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'daily_summary': daily_summary,
    }

    return render(
        request,
        'employees/attendance_history.html',
        context
    )




@login_required
def class_list(request):

    if not is_admin(request.user):
        return redirect('dashboard')

    classes = ClassSection.objects.all().prefetch_related(
        'faculty',
        'students'
    )

    return render(
        request,
        'employees/class_list.html',
        {
            'classes': classes
        }
    )


@login_required
def class_create(request):

    if not is_admin(request.user):
        return redirect('dashboard')

    if request.method == 'POST':

        form = ClassSectionForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect('class_list')

    else:

        form = ClassSectionForm()

    return render(
        request,
        'employees/class_form.html',
        {
            'form': form,
            'title': 'Add Class'
        }
    )


@login_required
def class_edit(request, pk):

    if not is_admin(request.user):
        return redirect('dashboard')

    class_section = get_object_or_404(
        ClassSection,
        pk=pk
    )

    if request.method == 'POST':

        form = ClassSectionForm(
            request.POST,
            instance=class_section
        )

        if form.is_valid():

            form.save()

            return redirect('class_list')

    else:

        form = ClassSectionForm(
            instance=class_section
        )

    return render(
        request,
        'employees/class_form.html',
        {
            'form': form,
            'title': 'Edit Class'
        }
    )


@login_required
def class_delete(request, pk):

    if not is_admin(request.user):
        return redirect('dashboard')

    class_section = get_object_or_404(
        ClassSection,
        pk=pk
    )

    if request.method == 'POST':

        class_section.delete()

        return redirect('class_list')

    return render(
        request,
        'employees/class_confirm_delete.html',
        {
            'class_section': class_section
        }
    )




@login_required
def daily_attendance(request):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        return redirect('dashboard')

    assigned_classes = request.user.profile.assigned_classes.all()

    selected_class_id = request.GET.get('class_id')
    selected_date = request.GET.get('date')

    records = Attendance.objects.none()

    if selected_class_id and selected_date:
        records = Attendance.objects.filter(
            student__class_section_id=selected_class_id,
            date=selected_date
        ).select_related(
            'student',
            'student__class_section',
            'subject'
        ).order_by('student__roll_number')

    total_students = records.values('student_id').distinct().count()
    present_count = records.filter(status='PRESENT').values('student_id').distinct().count()
    absent_count = records.filter(status='ABSENT').values('student_id').distinct().count()

    attendance_percentage = (
        (present_count / total_students) * 100
        if total_students > 0
        else 0
    )

    context = {
        'assigned_classes': assigned_classes,
        'selected_class_id': selected_class_id,
        'selected_date': selected_date,
        'records': records,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
    }

    return render(
        request,
        'employees/daily_attendance.html',
        context
    )




@login_required
def period_attendance(request):
    if not (
        hasattr(request.user, 'profile')
        and request.user.profile.role == 'FACULTY'
    ):
        return redirect('dashboard')

    assigned_classes = request.user.profile.assigned_classes.all()

    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')
    selected_date = request.GET.get('date')

    subjects = Subject.objects.filter(
        class_section__in=assigned_classes
    ).select_related('class_section').order_by(
        'class_section', 'code'
    )

    if selected_class_id:
        subjects = subjects.filter(
            class_section_id=selected_class_id
        )

    context = {
        'assigned_classes': assigned_classes,
        'subjects': subjects,
        'selected_class_id': selected_class_id,
        'selected_subject_id': selected_subject_id,
        'selected_date': selected_date,
    }

    return render(
        request,
        'employees/period_attendance.html',
        context
    )
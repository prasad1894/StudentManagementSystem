from django import forms
from django.contrib.auth.models import User
from .models import Employee, Task, LeaveRequest, Student, Subject, ClassSection, UserProfile


class EmployeeForm(forms.ModelForm):

    class Meta:
        model = Employee

        fields = [
            'employee_id',
            'name',
            'email',
            'phone',
            'department',
            'designation',
            'joining_date',
            'salary',
            'is_active',
        ]

        widgets = {
            'joining_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'class_section',
            'priority',
            'status',
            'due_date',
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'profile'):
            if user.profile.role == 'FACULTY':
                self.fields['class_section'].queryset = (
                    self.fields['class_section'].queryset.filter(
                        faculty=user.profile
                    )
                )


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = [
            'student',
            'leave_type',
            'start_date',
            'end_date',
            'reason',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'profile'):
            if user.profile.role == 'FACULTY':
                self.fields['student'].queryset = Student.objects.filter(
                    class_section__faculty=user.profile,
                    is_active=True
                ).order_by('roll_number')


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput
    )

    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
        ]

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError(
                    'Passwords do not match.'
                )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data['password']
        )

        if commit:
            user.save()

        return user


class StudentForm(forms.ModelForm):

    class Meta:
        model = Student
        fields = [
            'roll_number',
            'name',
            'email',
            'phone',
            'class_section',
            'admission_year',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'profile'):
            if user.profile.role == 'FACULTY':
                self.fields['class_section'].queryset = (
                    self.fields['class_section'].queryset.filter(
                        faculty=user.profile
                    )
                )



class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'class_section', 'faculty']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'profile'):
            if user.profile.role == 'FACULTY':
                self.fields['class_section'].queryset = (
                    self.fields['class_section'].queryset.filter(
                        faculty=user.profile
                    )
                )

                self.fields['faculty'].queryset = (
                    self.fields['faculty'].queryset.filter(
                        id=user.profile.id
                    )
                )
            elif user.profile.role == 'ADMIN':
                self.fields['faculty'].queryset = (
                    self.fields['faculty'].queryset.filter(
                        role='FACULTY'
                    )
                )



class ClassSectionForm(forms.ModelForm):

    class Meta:
        model = ClassSection
        fields = ['year', 'branch', 'section', 'faculty']

        widgets = {
            'year': forms.Select(),
            'branch': forms.TextInput(
                attrs={'placeholder': 'Example: CSM'}
            ),
            'section': forms.TextInput(
                attrs={'placeholder': 'Example: A'}
            ),
            'faculty': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['faculty'].queryset = UserProfile.objects.filter(
            role='FACULTY',
            user__is_active=True
        ).select_related('user')

    def clean(self):
        cleaned_data = super().clean()

        year = cleaned_data.get('year')
        branch = cleaned_data.get('branch')
        section = cleaned_data.get('section')

        if year and branch and section:
            queryset = ClassSection.objects.filter(
                year=year,
                branch__iexact=branch.strip(),
                section__iexact=section.strip()
            )

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    'This class already exists.'
                )

        return cleaned_data
# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import User, University, Subject, Enrollment, Grade


def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                return HttpResponseForbidden(
                    f"Вы вошли как {request.user.username} с ролью '{request.user.role}', "
                    f"но для доступа к этой странице требуется роль: {', '.join(roles)}."
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Успешный вход как {user.username} с ролью {user.role}')
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'professor':
                return redirect('professor_dashboard')
            return redirect('student_dashboard')
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Пароль неверный')
            else:
                messages.error(request, 'Пользователь с таким логином не найден')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('login')


@login_required
@role_required('admin')
def admin_dashboard(request):
    university = request.user.university
    students = User.objects.filter(university=university, role='student')
    professors = User.objects.filter(university=university, role='professor')
    subjects = Subject.objects.filter(university=university)

    context = {
        'university': university,
        'students': students,
        'professors': professors,
        'subjects': subjects,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@role_required('admin')
def register_student(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Студент с таким логином уже существует')
        else:
            User.objects.create_user(
                username=username,
                password=password,
                role='student',
                university=request.user.university
            )
            messages.success(request, f'Студент {username} успешно зарегистрирован')
        return redirect('admin_dashboard')
    return render(request, 'register_student.html')


@login_required
@role_required('admin')
def register_professor(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Преподаватель с таким логином уже существует')
        else:
            User.objects.create_user(
                username=username,
                password=password,
                role='professor',
                university=request.user.university
            )
            messages.success(request, f'Преподаватель {username} успешно зарегистрирован')
        return redirect('admin_dashboard')
    return render(request, 'register_professor.html')


@login_required
@role_required('admin')
def register_subject(request):
    if request.method == 'POST':
        name = request.POST['name']
        code = request.POST['code']
        if Subject.objects.filter(code=code, university=request.user.university).exists():
            messages.error(request, 'Предмет с таким кодом уже существует')
        else:
            Subject.objects.create(
                name=name,
                code=code,
                university=request.user.university,
                is_mandatory=False
            )
            messages.success(request, f'Предмет {name} успешно зарегистрирован')
        return redirect('admin_dashboard')
    return render(request, 'register_subject.html')


@login_required
@role_required('admin')
def assign_professor_to_subject(request, professor_id, subject_id):
    professor = User.objects.get(id=professor_id, role='professor', university=request.user.university)
    subject = Subject.objects.get(id=subject_id, university=request.user.university)
    if subject.professor is None:
        subject.professor = professor
        subject.save()
        messages.success(request, f'{professor.username} назначен на {subject.name}')
    else:
        messages.error(request, f'Предмет {subject.name} уже занят преподавателем {subject.professor.username}')
    return redirect('admin_dashboard')


@login_required
@role_required('student')
def student_dashboard(request):
    university = request.user.university
    enrollments = Enrollment.objects.filter(student=request.user)
    grades = Grade.objects.filter(enrollment__in=enrollments)
    available_subjects = Subject.objects.filter(university=university).exclude(
        id__in=enrollments.values_list('subject_id', flat=True)
    )
    gpa = request.user.calculate_gpa()
    status = request.user.get_academic_status()

    if request.method == 'POST':
        subject_id = request.POST['subject_id']
        subject = Subject.objects.get(id=subject_id, university=university)
        Enrollment.objects.create(student=request.user, subject=subject, semester=1)
        messages.success(request, f'Вы зарегистрированы на {subject.name}')
        return redirect('student_dashboard')

    context = {
        'enrollments': enrollments,
        'grades': grades,
        'available_subjects': available_subjects,
        'gpa': gpa,
        'status': status,
    }
    return render(request, 'student_dashboard.html', context)


@login_required
@role_required('professor')
def professor_dashboard(request):
    university = request.user.university
    professor_subjects = Subject.objects.filter(professor=request.user)
    available_subjects = Subject.objects.filter(university=university, professor__isnull=True)

    if request.method == 'POST':
        if 'enrollment_id' in request.POST:  # Выставление оценки
            enrollment_id = request.POST['enrollment_id']
            score = float(request.POST['score'])
            if 0 <= score <= 100:
                enrollment = Enrollment.objects.get(id=enrollment_id, subject__professor=request.user)
                Grade.objects.create(enrollment=enrollment, score=score)
                messages.success(request, f'Оценка {score} выставлена для {enrollment.student.username}')
            else:
                messages.error(request, 'Оценка должна быть от 0 до 100')
        elif 'subject_id' in request.POST:  # Регистрация на предмет
            subject_id = request.POST['subject_id']
            subject = Subject.objects.get(id=subject_id, university=university, professor__isnull=True)
            subject.professor = request.user
            subject.save()
            messages.success(request, f'Вы взяли предмет {subject.name}')
        return redirect('professor_dashboard')

    context = {
        'professor_subjects': professor_subjects,
        'available_subjects': available_subjects,
    }
    return render(request, 'professor_dashboard.html', context)
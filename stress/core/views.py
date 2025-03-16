from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import *


def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                return HttpResponseForbidden(
                    f"You are logged in as {request.user.username} with role '{request.user.role}', "
                    f"but this page requires role: {', '.join(roles)}."
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def login_view(request):
    notification = request.GET.get('notification')
    notification_type = request.GET.get('notification_type')
    has_unread_notifications = request.user.is_authenticated and request.user.notifications.filter(
        is_read=False).exists()

    if request.method == 'POST' and 'login' in request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            notification = 'Username and password are required'
            notification_type = 'error'
        else:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                notification = f'Logged in as {user.username} with role {user.role}'
                notification_type = 'success'
                if user.role == 'admin':
                    return redirect(f"/admin/?notification={notification}&notification_type={notification_type}")
                elif user.role == 'professor':
                    return redirect(f"/professor/?notification={notification}&notification_type={notification_type}")
                else:  # студент
                    return redirect(f"/student/?notification={notification}&notification_type={notification_type}")
            else:
                if User.objects.filter(username=username).exists():
                    notification = 'Incorrect password'
                else:
                    notification = 'User with this login not found'
                notification_type = 'error'

    return render(request, 'login.html', {
        'notification': notification,
        'notification_type': notification_type,
        'has_unread_notifications': has_unread_notifications,
    })


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@role_required('admin')
def register_student(request):
    notification = None
    notification_type = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            notification = 'Student with this login already exists'
            notification_type = 'error'
        else:
            student = User.objects.create_user(
                username=username,
                password=password,
                role='student',
                university=request.user.university
            )
            mandatory_subjects = Subject.objects.filter(university=request.user.university, is_mandatory=True)
            for subject in mandatory_subjects:
                Enrollment.objects.get_or_create(student=student, subject=subject, semester=1)
            notification = f'Student {username} registered and enrolled in mandatory subjects'
            notification_type = 'success'
            return render(request, 'admin_dashboard.html', {
                'university': request.user.university,
                'students': User.objects.filter(university=request.user.university, role='student'),
                'professors': User.objects.filter(university=request.user.university, role='professor'),
                'subjects': Subject.objects.filter(university=request.user.university),
                'notification': notification,
                'notification_type': notification_type,
            })
    return render(request, 'register_student.html',
                  {'notification': notification, 'notification_type': notification_type})


@login_required
@role_required('admin')
def register_professor(request):
    notification = None
    notification_type = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if not Subject.objects.filter(university=request.user.university, professor__isnull=True).exists():
            notification = 'All subjects already have professors. Cannot add a new professor.'
            notification_type = 'error'
            return render(request, 'admin_dashboard.html', {
                'university': request.user.university,
                'students': User.objects.filter(university=request.user.university, role='student'),
                'professors': User.objects.filter(university=request.user.university, role='professor'),
                'subjects': Subject.objects.filter(university=request.user.university),
                'notification': notification,
                'notification_type': notification_type,
            })
        if User.objects.filter(username=username).exists():
            notification = 'Professor with this login already exists'
            notification_type = 'error'
        else:
            User.objects.create_user(
                username=username,
                password=password,
                role='professor',
                university=request.user.university
            )
            notification = f'Professor {username} successfully registered'
            notification_type = 'success'
            return render(request, 'admin_dashboard.html', {
                'university': request.user.university,
                'students': User.objects.filter(university=request.user.university, role='student'),
                'professors': User.objects.filter(university=request.user.university, role='professor'),
                'subjects': Subject.objects.filter(university=request.user.university),
                'notification': notification,
                'notification_type': notification_type,
            })
    return render(request, 'register_professor.html',
                  {'notification': notification, 'notification_type': notification_type})


@login_required
@role_required('admin')
def register_subject(request):
    notification = None
    notification_type = None
    if request.method == 'POST':
        name = request.POST['name']
        code = request.POST['code']
        if Subject.objects.filter(code=code, university=request.user.university).exists():
            notification = 'Subject with this code already exists'
            notification_type = 'error'
        else:
            Subject.objects.create(
                name=name,
                code=code,
                university=request.user.university,
                is_mandatory=False
            )
            notification = f'Subject {name} successfully registered'
            notification_type = 'success'
            return render(request, 'admin_dashboard.html', {
                'university': request.user.university,
                'students': User.objects.filter(university=request.user.university, role='student'),
                'professors': User.objects.filter(university=request.user.university, role='professor'),
                'subjects': Subject.objects.filter(university=request.user.university),
                'notification': notification,
                'notification_type': notification_type,
            })
    return render(request, 'register_subject.html',
                  {'notification': notification, 'notification_type': notification_type})


@login_required
@role_required('admin')
def assign_professor_to_subject(request, professor_id, subject_id):
    professor = User.objects.get(id=professor_id, role='professor', university=request.user.university)
    subject = Subject.objects.get(id=subject_id, university=request.user.university)
    total_subjects = Subject.objects.filter(university=request.user.university).count()
    total_professors = User.objects.filter(university=request.user.university, role='professor').count()
    professor_subjects = Subject.objects.filter(professor=professor).count()
    max_subjects_per_professor = total_subjects - (total_professors - 1)

    notification = None
    notification_type = None
    if subject.professor is None:
        if professor_subjects >= max_subjects_per_professor:
            notification = f'{professor.username} cannot take more than {max_subjects_per_professor} subjects.'
            notification_type = 'error'
        else:
            subject.professor = professor
            subject.save()
            notification = f'{professor.username} assigned to {subject.name}'
            notification_type = 'success'
    else:
        notification = f'Subject {subject.name} is already assigned to {subject.professor.username}'
        notification_type = 'error'
    return render(request, 'admin_dashboard.html', {
        'university': request.user.university,
        'students': User.objects.filter(university=request.user.university, role='student'),
        'professors': User.objects.filter(university=request.user.university, role='professor'),
        'subjects': Subject.objects.filter(university=request.user.university),
        'notification': notification,
        'notification_type': notification_type,
    })


@login_required
@role_required('admin')
def remove_professor_from_subject(request, subject_id):
    subject = Subject.objects.get(id=subject_id, university=request.user.university)
    current_professor = subject.professor
    if current_professor:
        professor_subjects_count = Subject.objects.filter(professor=current_professor).count()
        if professor_subjects_count <= 1:
            return render(request, 'admin_dashboard.html', {
                'university': request.user.university,
                'students': User.objects.filter(university=request.user.university, role='student'),
                'professors': User.objects.filter(university=request.user.university, role='professor'),
                'subjects': Subject.objects.filter(university=request.user.university),
                'notification': f'Cannot remove {subject.name} from {current_professor.username}, it is their last subject.',
                'notification_type': 'error',
            })

        if request.method == 'POST' and 'confirm' in request.POST:
            Grade.objects.filter(enrollment__subject=subject).delete()
            subject.professor = None
            subject.save()
            return render(request, 'admin_dashboard.html', {
                'university': request.user.university,
                'students': User.objects.filter(university=request.user.university, role='student'),
                'professors': User.objects.filter(university=request.user.university, role='professor'),
                'subjects': Subject.objects.filter(university=request.user.university),
                'notification': f'Subject {subject.name} freed. All student grades removed.',
                'notification_type': 'success',
            })

        return render(request, 'confirm_remove_professor.html', {
            'subject': subject,
            'current_professor': current_professor.username,
        })
    return render(request, 'admin_dashboard.html', {
        'university': request.user.university,
        'students': User.objects.filter(university=request.user.university, role='student'),
        'professors': User.objects.filter(university=request.user.university, role='professor'),
        'subjects': Subject.objects.filter(university=request.user.university),
        'notification': 'This subject has no professor.',
        'notification_type': 'error',
    })


@login_required
@role_required('student')
def student_dashboard(request):
    university = request.user.university
    enrollments = Enrollment.objects.filter(student=request.user).select_related('subject__professor')
    grades = Grade.objects.filter(enrollment__in=enrollments)
    available_subjects = Subject.objects.filter(university=university).exclude(
        id__in=enrollments.values_list('subject_id', flat=True)
    )
    gpa = request.user.calculate_gpa()
    status = request.user.get_academic_status()

    notification = request.GET.get('notification')
    notification_type = request.GET.get('notification_type')
    has_unread_notifications = request.user.notifications.filter(is_read=False).exists()

    if request.method == 'POST':
        if 'subject_id' in request.POST:
            subject_id = request.POST['subject_id']
            subject = Subject.objects.get(id=subject_id, university=university)
            Enrollment.objects.create(student=request.user, subject=subject, semester=1)
            notification = f'You have enrolled in {subject.name}'
            notification_type = 'success'
            return redirect(f"/student/?notification={notification}&notification_type={notification_type}")
        elif 'application' in request.POST:
            # Проверка обязательных предметов с оценкой ниже 60
            mandatory_grades = Grade.objects.filter(
                enrollment__student=request.user,
                enrollment__subject__is_mandatory=True
            )
            for grade in mandatory_grades:
                if grade.score < 60:
                    Notification.objects.create(
                        recipient=request.user,
                        message=f"Your application was denied: {grade.enrollment.subject.name} ({grade.enrollment.subject.code}) grade is {grade.score} (below 60)",
                        action='application_denied'
                    )
                    notification = f'Application denied: {grade.enrollment.subject.name} grade is below 60'
                    notification_type = 'error'
                    return redirect(f"/student/?notification={notification}&notification_type={notification_type}")

            # Проверка предметов без оценок
            enrollments_without_grades = Enrollment.objects.filter(
                student=request.user
            ).exclude(id__in=grades.values('enrollment_id'))
            if enrollments_without_grades.exists():
                without_grade_subject = enrollments_without_grades.first().subject
                Notification.objects.create(
                    recipient=request.user,
                    message=f"Your application was denied: {without_grade_subject.name} ({without_grade_subject.code}) has no grade",
                    action='application_denied'
                )
                notification = f'Application denied: {without_grade_subject.name} has no grade'
                notification_type = 'error'
                return redirect(f"/student/?notification={notification}&notification_type={notification_type}")

            # Если всё в порядке, создаём запрос для админа
            admin = User.objects.filter(university=university, role='admin').first()
            if admin:
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    message=f"{request.user.username} submitted an application with GPA {gpa:.2f}",
                    action='application_submitted',
                    is_read=True
                )
                notification = 'Application submitted to admin'
                notification_type = 'success'
            else:
                notification = 'No admin available to process application'
                notification_type = 'error'
            return redirect(f"/student/?notification={notification}&notification_type={notification_type}")
        elif 'request_grade' in request.POST:
            enrollment_id = request.POST['enrollment_id']
            enrollment = Enrollment.objects.get(id=enrollment_id, student=request.user)
            professor = enrollment.subject.professor
            if professor:
                Notification.objects.create(
                    recipient=professor,
                    sender=request.user,
                    message=f"{request.user.username} requests a grade for {enrollment.subject.name} ({enrollment.subject.code})",
                    action='grade_request',
                    is_read=True
                )
                notification = f'Request sent to {professor.username} for {enrollment.subject.name}'
                notification_type = 'success'
            else:
                notification = 'No professor assigned to this subject'
                notification_type = 'error'
            return redirect(f"/student/?notification={notification}&notification_type={notification_type}")

    return render(request, 'student_dashboard.html', {
        'enrollments': enrollments,
        'grades': grades,
        'available_subjects': available_subjects,
        'gpa': gpa,
        'status': status,
        'notification': notification,
        'notification_type': notification_type,
        'has_unread_notifications': has_unread_notifications,
    })


@login_required
@role_required('professor')
def professor_dashboard(request):
    university = request.user.university
    professor_subjects = Subject.objects.filter(professor=request.user)
    available_subjects = Subject.objects.filter(university=university, professor__isnull=True)
    total_subjects = Subject.objects.filter(university=university).count()
    total_professors = User.objects.filter(university=university, role='professor').count()
    professor_subjects_count = professor_subjects.count()
    max_subjects_per_professor = total_subjects - (total_professors - 1) if total_professors > 1 else total_subjects
    grade_requests = Notification.objects.filter(
        recipient=request.user,
        action='grade_request'
    )  # Запросы на оценки от студентов (все, не только непрочитанные)

    notification = request.GET.get('notification')
    notification_type = request.GET.get('notification_type')
    has_unread_notifications = request.user.notifications.filter(is_read=False).exists()

    if request.method == 'POST':
        if 'enrollment_id' in request.POST:
            enrollment_id = request.POST['enrollment_id']
            score = float(request.POST['score'])
            if 0 <= score <= 100:
                enrollment = Enrollment.objects.get(id=enrollment_id, subject__professor=request.user)
                grade, created = Grade.objects.update_or_create(
                    enrollment=enrollment,
                    defaults={'score': score}
                )
                action = "updated" if not created else "set"
                Notification.objects.create(
                    recipient=enrollment.student,
                    sender=request.user,
                    message=f"Your grade for {enrollment.subject.name} ({enrollment.subject.code}) has been {action}: {score}",
                    action='grade_set'
                )
                notification = f'Grade {score} {action} for {enrollment.student.username}'
                notification_type = 'success'
            else:
                notification = 'Grade must be between 0 and 100'
                notification_type = 'error'
            return redirect(f"/professor/?notification={notification}&notification_type={notification_type}")
        elif 'subject_id' in request.POST:
            subject_id = request.POST['subject_id']
            subject = Subject.objects.get(id=subject_id, university=university, professor__isnull=True)
            if professor_subjects_count >= max_subjects_per_professor:
                notification = f'You cannot take more than {max_subjects_per_professor} subjects.'
                notification_type = 'error'
            else:
                subject.professor = request.user
                subject.save()
                notification = f'You have taken {subject.name} ({subject.code})'
                notification_type = 'success'
            return redirect(f"/professor/?notification={notification}&notification_type={notification_type}")

    return render(request, 'professor_dashboard.html', {
        'professor_subjects': professor_subjects,
        'available_subjects': available_subjects,
        'grade_requests': grade_requests,
        'notification': notification,
        'notification_type': notification_type,
    })


@login_required
@role_required('admin')
def admin_dashboard(request):
    university = request.user.university
    students = User.objects.filter(university=university, role='student')
    professors = User.objects.filter(university=university, role='professor')
    subjects = Subject.objects.filter(university=university)
    pending_applications = Notification.objects.filter(
        recipient=request.user,
        action='application_submitted'
    )

    notification = request.GET.get('notification')
    notification_type = request.GET.get('notification_type')
    has_unread_notifications = request.user.notifications.filter(is_read=False).exists()

    if request.method == 'POST' and 'notification_id' in request.POST:
        notif_id = request.POST['notification_id']
        action = request.POST.get('action')
        notif = Notification.objects.get(id=notif_id, recipient=request.user, action='application_submitted')
        student = notif.sender
        if action == 'confirm':
            Notification.objects.create(
                recipient=student,
                sender=request.user,
                message=f"Congrats, {student.username}! Your grades are top-notch!",
                action='application_confirmed'
            )
            notification = f"Application of {student.username} confirmed"
            notification_type = 'success'
            notif.delete()
        elif action == 'cancel':
            reason = request.POST.get('reason', 'No reason provided')
            Notification.objects.create(
                recipient=student,
                sender=request.user,
                message=f"Unfortunately, {student.username}, your request has been denied: {reason}",
                action='application_cancelled'
            )
            notification = f"Application of {student.username} cancelled"
            notification_type = 'error'
            notif.delete()
        return redirect(f"/admin/?notification={notification}&notification_type={notification_type}")

    return render(request, 'admin_dashboard.html', {
        'university': university,
        'students': students,
        'professors': professors,
        'subjects': subjects,
        'pending_applications': pending_applications,
        'notification': notification,
        'notification_type': notification_type,
    })


@login_required
@role_required('admin')
def application_details(request, notification_id):
    notif = Notification.objects.get(id=notification_id, recipient=request.user, action='application_submitted')
    student = notif.sender
    enrollments = Enrollment.objects.filter(student=student).select_related('subject')
    grades = Grade.objects.filter(enrollment__in=enrollments)

    return render(request, 'application_details.html', {
        'student': student,
        'enrollments': enrollments,
        'grades': grades,
        'notification_id': notification_id,
    })


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    has_unread_notifications = notifications.filter(is_read=False).exists()
    if request.method == 'POST' and 'mark_read' in request.POST:
        notifications.update(is_read=True)
        return redirect('notifications')

    return render(request, 'notifications.html', {
        'notifications': notifications,
        'has_unread_notifications': has_unread_notifications,
    })
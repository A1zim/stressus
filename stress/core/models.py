# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class University(models.Model):
    NAME_CHOICES = (
        ('university1', 'University 1'),
        ('university2', 'University 2'),
        ('university3', 'University 3'),
    )
    name = models.CharField(max_length=20, choices=NAME_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('professor', 'Professor'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    university = models.ForeignKey(University, on_delete=models.CASCADE)

    def calculate_gpa(self):
        grades = Grade.objects.filter(enrollment__student=self)
        return grades.aggregate(models.Avg('score'))['score__avg'] or 0

    def get_academic_status(self):
        gpa = self.calculate_gpa()
        enrollments_count = Enrollment.objects.filter(student=self).count()
        return 'passed' if gpa > 60 and enrollments_count >= 4 else 'failed'

    def __str__(self):
        return self.username

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=False)
    professor = models.ForeignKey(User, on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 limit_choices_to={'role': 'professor'},
                                 related_name='subjects')

    class Meta:
        unique_together = ('code', 'university')

    def __str__(self):
        return f"{self.name} ({self.code})"

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='enrollments',
                              limit_choices_to={'role': 'student'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('student', 'subject', 'semester')

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    date_added = models.DateTimeField(auto_now_add=True)
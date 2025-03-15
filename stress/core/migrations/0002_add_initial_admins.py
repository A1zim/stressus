# core/migrations/0002_add_initial_data.py
from django.db import migrations

def create_initial_data(apps, schema_editor):
    University = apps.get_model('core', 'University')
    Subject = apps.get_model('core', 'Subject')
    User = apps.get_model('core', 'User')

    universities = ['university1', 'university2', 'university3']
    for uni_name in universities:
        University.objects.get_or_create(name=uni_name)

    admin_data = [
        {'username': 'admin1', 'password': 'adminpass123', 'university': 'university1'},
        {'username': 'admin2', 'password': 'adminpass123', 'university': 'university2'},
        {'username': 'admin3', 'password': 'adminpass123', 'university': 'university3'},
    ]
    for admin in admin_data:
        university = University.objects.get(name=admin['university'])
        if not User.objects.filter(username=admin['username']).exists():
            User.objects.create_superuser(
                username=admin['username'],
                password=admin['password'],
                email=f"{admin['username']}@example.com",
                role='admin',
                university=university
            )

    mandatory_subjects = [
        {'name': 'Математика', 'code': 'MATH101'},
        {'name': 'Физика', 'code': 'PHYS101'},
        {'name': 'Программирование', 'code': 'CS101'},
        {'name': 'История', 'code': 'HIST101'},
        {'name': 'Английский', 'code': 'ENG101'},
    ]
    for uni in University.objects.all():
        for subj in mandatory_subjects:
            Subject.objects.get_or_create(
                name=subj['name'],
                code=subj['code'],
                university=uni,
                is_mandatory=True
            )

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
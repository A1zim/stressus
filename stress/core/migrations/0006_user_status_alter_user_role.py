# Generated by Django 5.1.7 on 2025-03-16 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_mandatorysubject_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('passed', 'Passed')], default='active', max_length=20),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('professor', 'Professor'), ('admin', 'Admin'), ('super_admin', 'Super Admin')], default='student', max_length=20),
        ),
    ]

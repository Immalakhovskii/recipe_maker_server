# Generated by Django 2.2.19 on 2022-09-16 01:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0011_auto_20220914_0457'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': ['name']},
        ),
        migrations.RemoveConstraint(
            model_name='ingredient',
            name='pair ingredient/measure must be unique',
        ),
    ]

# Generated by Django 2.2.19 on 2022-09-08 13:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20220908_1625'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ingredientamount',
            unique_together={('ingredient', 'recipe')},
        ),
    ]

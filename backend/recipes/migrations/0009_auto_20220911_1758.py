# Generated by Django 2.2.19 on 2022-09-11 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20220911_0627'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='tag', to='recipes.Tag', verbose_name='recipe tags'),
        ),
    ]

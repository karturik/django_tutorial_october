# Generated by Django 4.2.7 on 2023-11-14 15:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_long', models.CharField(help_text='Full Language title of the book', max_length=50)),
                ('language_short', models.CharField(help_text='Short Language title of the book', max_length=2)),
            ],
        ),
        migrations.AddField(
            model_name='bookinstance',
            name='language',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.language'),
        ),
    ]
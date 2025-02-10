# Generated by Django 4.2.19 on 2025-02-10 06:50

import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=900, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('image1', models.URLField(blank=True, null=True)),
                ('image2', models.URLField(blank=True, null=True)),
                ('image3', models.URLField(blank=True, null=True)),
                ('image4', models.URLField(blank=True, null=True)),
                ('size', models.CharField(blank=True, choices=[('inches', 'Inches'), ('feet', 'Feet')], default='inches', max_length=100, null=True)),
                ('standard_size', models.CharField(blank=True, max_length=500, null=True)),
                ('width', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('height', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product_specifications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=900, null=True)),
                ('description', models.CharField(blank=True, max_length=900, null=True)),
                ('thickness', models.CharField(blank=True, max_length=900, null=True)),
                ('material', models.CharField(blank=True, max_length=900, null=True)),
                ('weight', models.CharField(blank=True, max_length=900, null=True)),
                ('drilled_holes', models.CharField(blank=True, max_length=900, null=True)),
                ('min_size', models.CharField(blank=True, max_length=900, null=True)),
                ('max_size', models.CharField(blank=True, max_length=900, null=True)),
                ('printing_options', models.CharField(blank=True, max_length=900, null=True)),
                ('cutting_options', models.CharField(blank=True, max_length=900, null=True)),
                ('common_sizes', models.CharField(blank=True, max_length=900, null=True)),
                ('installation', models.CharField(blank=True, max_length=900, null=True)),
                ('shape', models.CharField(blank=True, max_length=900, null=True)),
                ('life_span', models.CharField(blank=True, max_length=900, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='specifications', to='products_app.product')),
            ],
        ),
        migrations.CreateModel(
            name='Product_overview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heading', models.CharField(blank=True, max_length=900, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='overview', to='products_app.product')),
            ],
        ),
        migrations.CreateModel(
            name='Product_installation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=900, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products_app.product')),
            ],
        ),
        migrations.CreateModel(
            name='Installation_steps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('steps', models.TextField(blank=True, null=True)),
                ('installation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products_app.product_installation')),
            ],
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('is_admin', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]

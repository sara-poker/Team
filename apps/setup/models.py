from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

from config import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, username, first_name, last_name, password=None, **extra_fields):
        if not username:
            raise ValueError('Username باید وارد شود')
        if not first_name or not last_name:
            raise ValueError('نام و نام خانوادگی باید وارد شوند')

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser باید is_staff=True داشته باشد.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser باید is_superuser=True داشته باشد.')

        return self.create_user(username, first_name, last_name, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    ROLE_CHOICES = (
        ('manager', 'Manager'),
        ('admin', 'Admin'),
        ('user', 'User'),
    )

    CONTRACT_TYPE_CHOICES = (
        ('hourly', 'ساعتی'),
        ('employee', 'کارمندی'),
        ('soldier', 'سرباز'),
    )

    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    contract_type = models.CharField(max_length=10, choices=CONTRACT_TYPE_CHOICES, default='employee')

    teams = models.ManyToManyField('Team', related_name='members_teams', blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name


class Team(models.Model):
    class Meta:
        verbose_name = 'تیم'
        verbose_name_plural = 'تیم‌ها'

    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_teams'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_all_members(self):
        members = list(self.members_teams.all())
        for sub_team in self.sub_teams.all():
            members.extend(sub_team.get_all_members())
        return members

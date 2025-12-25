from django.core.validators import MinValueValidator, MaxValueValidator

from django.db import models
from django.db.models import Avg
from django.utils import timezone

from datetime import datetime, timedelta
from config import settings
from apps.setup.models import Team




class Project(models.Model):
    class Meta:
        verbose_name = 'پروژه'
        verbose_name_plural = 'پروژه‌ها'

    STATUS_PROJECT = (
        ('not_started', 'Not started'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
    )

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_PROJECT, default='not_started')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members_projects', blank=True)
    teams = models.ManyToManyField(Team, related_name='teams_projects', blank=True)


    def get_overdue_tasks(self):
        """دریافت تسک‌های تأخیر داشته"""
        return self.task_set.filter(
            deadline__lt=datetime.now().date(),
            status__in=['in_progress', 'not_started']
        )

    def get_project_progress(self):
        return self.task_set.aggregate(avg=Avg('percent'))['avg'] or 0

    def get_project_duration(self):
        """محاسبه مدت زمان پروژه"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    def get_assignees(self):
        """دریافت تمام کاربران اختصاص داده شده به پروژه"""
        assignees = set()
        for task in self.get_all_tasks():
            assignees.update(task.assignees.all())
        return list(assignees)

    def __str__(self):
        return f"پروژه: {self.title}"


class Task(models.Model):
    class Meta:
        verbose_name = 'تسک'
        verbose_name_plural = 'تسک‌ها'

    STATUS_TASK = (
        ('not_started', 'Not started'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    percent = models.FloatField(
        default=0.0,
        validators=[
            MinValueValidator(0.0, message="درصد نمی‌تواند کمتر از 0 باشد"),
            MaxValueValidator(100.0, message="درصد نمی‌تواند بیشتر از 100 باشد")
        ]
    )
    status = models.CharField(max_length=20, choices=STATUS_TASK, default='not_started')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    weight = models.IntegerField(
        default=1,
        validators=[
            MinValueValidator(1, message="وزن نمی‌تواند کمتر از 1 باشد"),
            MaxValueValidator(10, message="وزن نمی‌تواند بیشتر از 10 باشد")
        ]
    )
    approval_status = models.BooleanField(default=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    assignees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_task_priority(self):
        """محاسبه اولویت تسک بر اساس وزن و deadline"""
        if not self.deadline:
            return self.weight

        days_remaining = self.get_time_remaining()
        if days_remaining is None:
            return self.weight

        # اولویت بالاتر برای تسک‌های نزدیک deadline
        priority_multiplier = max(1, 10 / max(days_remaining, 1))
        return self.weight * priority_multiplier

    def get_task_assignees_count(self):
        return self.assignees.count()

    def get_time_difference(self):
        if self.deadline and self.status != 'completed':
            today = datetime.now().date()
            if self.deadline < today:
                days_diff = (today - self.deadline).days
                return timedelta(days=days_diff)
            elif self.deadline > today:
                days_diff = (self.deadline - today).days
                return -timedelta(days=days_diff)
        return None

    def sync_task_status_and_percent(self):
        if self.percent >= 100 and self.status != 'completed':
            self.status = 'completed'

        elif self.status == 'completed' and self.percent < 100:
            self.percent = 100

        self.save()

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

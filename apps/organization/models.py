from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from config import settings
from apps.setup.models import Team


class Project(models.Model):
    class Meta:
        verbose_name = 'پروژه'
        verbose_name_plural = 'پروژه ها'

    STATUS_PROJECT = (
        ('not_started', 'Not started'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    percent = models.FloatField(
        default=0.0,
        validators=[
            MinValueValidator(0.0, message="درصد نمی‌تواند کمتر از 0 باشد"),
            MaxValueValidator(100.0, message="درصد نمی‌تواند بیشتر از 100 باشد")
        ]
    )
    status = models.CharField(max_length=10, choices=STATUS_PROJECT, default='not_started')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members_projects', blank=True, null=True)
    teams = models.ManyToManyField(Team, related_name='teams_projects', blank=True, null=True)

    def __str__(self):
        return "پروژه" + self.title

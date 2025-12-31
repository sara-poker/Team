from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Project, Team, Task
User = get_user_model()


def clear_project_cache_for_user(user):
    """پاک کردن کش پروژه برای یک کاربر خاص"""
    if user:
        cache_key = f"projects_submenu_{user.id}_{user.role}"
        cache.delete(cache_key)


def clear_cache_for_all_related_users(project):
    """کمکی برای پیدا کردن تمام افراد مرتبط با یک پروژه و پاک کردن کش آن‌ها"""
    # ۱. کاربرانی که مستقیم عضو هستند
    for user in project.members.all():
        clear_project_cache_for_user(user)

    # ۲. تمام اعضای تیم‌هایی که به این پروژه وصل هستند
    for team in project.teams.all():
        for user in team.members_teams.all():
            clear_project_cache_for_user(user)


# --- SIGNALS ---

@receiver(post_save, sender=Project)
def clear_cache_on_project_save(sender, instance, **kwargs):
    # زمان ایجاد یا ویرایش عنوان پروژه
    clear_cache_for_all_related_users(instance)


@receiver(pre_delete, sender=Project)
def clear_cache_before_project_delete(sender, instance, **kwargs):
    # بسیار مهم: قبل از حذف پروژه، لیست افراد را می‌گیریم و کش را پاک می‌کنیم
    clear_cache_for_all_related_users(instance)


@receiver(m2m_changed, sender=Project.members.through)
def clear_cache_on_members_m2m_change(sender, instance, action, pk_set, **kwargs):
    """وقتی کاربری به پروژه اضافه یا حذف می‌شود"""
    if action in ["post_add", "post_remove", "post_clear"]:
        # در m2m_changed، instance همان شیء Project است
        clear_cache_for_all_related_users(instance)
        # اگر کاربر خاصی حذف شده باشد، برای اطمینان بیشتر:
        if pk_set:
            for pk in pk_set:
                user = User.objects.filter(pk=pk).first()
                clear_project_cache_for_user(user)


@receiver(m2m_changed, sender=Project.teams.through)
def clear_cache_on_teams_m2m_change(sender, instance, action, pk_set, **kwargs):
    """وقتی تیمی به پروژه اضافه یا حذف می‌شود"""
    if action in ["post_add", "post_remove", "post_clear"]:
        clear_cache_for_all_related_users(instance)
        # پاک کردن کش اعضای تیم‌های تغییر یافته
        if pk_set:
            teams = Team.objects.filter(pk__in=pk_set)
            for team in teams:
                for user in team.members_teams.all():
                    clear_project_cache_for_user(user)

@receiver(m2m_changed, sender=User.teams.through)
def clear_cache_when_team_membership_changes(sender, instance, action, pk_set, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        # instance اینجا Team است
        # پیدا کردن تمام پروژه‌هایی که این تیم در آن‌ها حضور دارد
        projects = instance.teams_projects.all()
        for proj in projects:
            clear_cache_for_all_related_users(proj)


@receiver(pre_save, sender=Task)
def sync_task_status_and_percent_signal(sender, instance, **kwargs):
    if instance.percent >= 100 and instance.status not in ['reviewing', 'completed']:
        instance.status = 'reviewing'
    elif instance.status in ['reviewing', 'completed'] and instance.percent < 100:
        instance.percent = 100

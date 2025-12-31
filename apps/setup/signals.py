from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from apps.organization.models import Project
from apps.setup.models import Team
from django.contrib.auth import get_user_model

User = get_user_model()


def clear_project_cache_for_user(user):
    """پاک کردن کش منوی پروژه‌ها برای کاربر"""
    if user:
        cache_key = f"projects_submenu_{user.id}_{user.role}"
        cache.delete(cache_key)


def clear_team_cache_for_user(user):
    """پاک کردن کش منوی تیم‌ها برای کاربر"""
    if user:
        cache_key = f"teams_submenu_user_{user.id}"
        cache.delete(cache_key)


def clear_all_caches_for_team_members(team):
    """پاک کردن هر دو نوع کش برای تمام اعضای یک تیم"""
    # استفاده از متد خودت برای گرفتن همه اعضا (حتی زیرتیم‌ها)
    all_members = team.get_all_members()
    for user in set(all_members):  # استفاده از set برای جلوگیری از تکرار
        clear_team_cache_for_user(user)
        clear_project_cache_for_user(user)


# ---------------- SIGNALS ---------------- #

@receiver(post_save, sender=Team)
def clear_team_cache_on_save(sender, instance, **kwargs):
    """زمان ایجاد یا تغییر نام تیم"""
    clear_all_caches_for_team_members(instance)


@receiver(pre_delete, sender=Team)
def clear_team_cache_on_delete(sender, instance, **kwargs):
    """
    قبل از حذف تیم:
    باید کش کاربران را پاک کنیم چون بعد از حذف،
    دسترسی به members_teams قطع می‌شود.
    """
    clear_all_caches_for_team_members(instance)


@receiver(m2m_changed, sender=User.teams.through)
def clear_team_cache_on_membership_change(sender, instance, action, pk_set, **kwargs):
    """
    وقتی کاربری به تیمی اضافه یا از آن حذف می‌شود.
    instance: می‌تواند کاربر باشد یا تیم (بسته به اینکه از کدام سمت تغییر ایجاد شود)
    """
    if action in ("post_add", "post_remove", "post_clear"):
        if isinstance(instance, User):
            # اگر تغییر از سمت کاربر باشد (user.teams.add)
            clear_team_cache_for_user(instance)
            clear_project_cache_for_user(instance)
        elif isinstance(instance, Team):
            # اگر تغییر از سمت تیم باشد (team.members_teams.add)
            clear_all_caches_for_team_members(instance)

        # اگر کاربرانی خاص (pk_set) تحت تاثیر قرار گرفته‌اند
        if pk_set:
            for pk in pk_set:
                u = User.objects.filter(pk=pk).first()
                clear_team_cache_for_user(u)
                clear_project_cache_for_user(u)


@receiver(m2m_changed, sender=Project.teams.through)
def clear_cache_on_project_team_assignment(sender, instance, action, pk_set, **kwargs):
    """
    وقتی یک تیم به یک پروژه اختصاص داده می‌شود یا حذف می‌شود.
    باید کش پروژه‌ی اعضای آن تیم پاک شود.
    """
    if action in ("post_add", "post_remove", "post_clear"):
        if pk_set:
            affected_teams = Team.objects.filter(pk__in=pk_set)
            for team in affected_teams:
                clear_all_caches_for_team_members(team)

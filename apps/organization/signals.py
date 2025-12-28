from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Team
from config import settings

User = settings.AUTH_USER_MODEL


def clear_team_cache_for_members(team):
    for user in team.members_teams.all():
        cache_key = f"teams_submenu_user_{user.id}"
        cache.delete(cache_key)


@receiver(post_save, sender=Team)
def clear_team_cache_on_save(sender, instance, **kwargs):
    clear_team_cache_for_members(instance)


@receiver(post_delete, sender=Team)
def clear_team_cache_on_delete(sender, instance, **kwargs):
    clear_team_cache_for_members(instance)


@receiver(m2m_changed, sender=User.teams.through)
def clear_team_cache_on_membership_change(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        cache_key = f"teams_submenu_user_{instance.id}"
        cache.delete(cache_key)

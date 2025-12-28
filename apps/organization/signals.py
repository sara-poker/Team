from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Team

CACHE_KEY = "projects_submenu"

@receiver(post_save, sender=Team)
def clear_team_cache_on_save(sender, instance, **kwargs):
    cache.delete(CACHE_KEY)


@receiver(post_delete, sender=Team)
def clear_team_cache_on_delete(sender, instance, **kwargs):
    print("TEAM SAVE SIGNAL FIRED3")
    cache.delete(CACHE_KEY)

from django.conf import settings
from django.core.cache import cache
from django.db.models import Exists, OuterRef
from apps.setup.models import Team

import copy
import json
import requests

from web_project.template_helpers.theme import TemplateHelper

API_BASE = settings.BASE_URL


def build_team(user):
    cache_key = "teams_submenu"
    submenu = cache.get(cache_key)

    if submenu is not None:
        return submenu

    try:
        qs = Team.objects.filter(members_teams=user).distinct()

        new_submenu = []
        for row in qs:
            new_submenu.append({
                "url": f"/team/{row.id}",
                "external": True,
                "name": row.name,
                "slug": "team_detail"
            })

        cache.set(cache_key, new_submenu, 60 * 60 * 24)
        return new_submenu

    except Exception as e:
        print(f"Error in build_team: {e}")
        return []

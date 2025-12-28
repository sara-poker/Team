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

def build_project(user):
    cache_key = f"projects_submenu_{user.id}_{user.role}"
    submenu = cache.get(cache_key)

    if submenu is not None:
        return submenu

    try:
        # manager و admin → پروژه‌های تیم‌ها
        if user.role in ('manager', 'admin'):
            projects = (
                Project.objects
                .filter(teams__members_teams=user)
                .distinct()
            )

        # user → پروژه‌های اساین‌شده به خودش
        else:
            projects = (
                Project.objects
                .filter(members=user)
                .distinct()
            )

        new_submenu = []
        for project in projects:
            new_submenu.append({
                "url": f"/project/{project.id}",
                "external": True,
                "name": project.title,
                "slug": "project_detail"
            })

        cache.set(cache_key, new_submenu, 60 * 60 * 24)
        return new_submenu

    except Exception as e:
        print(f"Error in build_project: {e}")
        return []

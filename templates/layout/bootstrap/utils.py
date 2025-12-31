from django.conf import settings
from django.core.cache import cache

from apps.setup.models import Team
from apps.organization.models import Project

API_BASE = settings.BASE_URL


def build_team(user):
    if not user or not user.is_authenticated:
        return []

    cache_key = f"teams_submenu_user_{user.id}"

    submenu = cache.get(cache_key)
    if submenu is not None:
        return submenu

    try:
        qs = Team.objects.filter(members_teams=user).distinct()
        print("Query to get all teams")

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
        if user.role in ('manager', 'admin'):
            projects = (
                Project.objects
                .filter(teams__members_teams=user)
                .distinct()
            )

        else:
            projects = (
                Project.objects
                .filter(members=user)
                .distinct()
            )

        print("Query to get all Project")
        new_submenu = []
        new_submenu_project = []
        for project in projects:
            new_submenu_project.append({
                "url": f"/projects/{project.id}",
                "external": True,
                "name": project.title,
                "slug": "project_detail"
            })
        new_submenu.append(new_submenu_project)

        new_submenu_project_tasks = []
        for project in projects:
            new_submenu_project_tasks.append({
                "url": f"/projects/{project.id}/tasks",
                "external": True,
                "name": "تسک های " + project.title,
                "slug": "project_detail",
            })
        new_submenu.append(new_submenu_project_tasks)

        cache.set(cache_key, new_submenu, 60 * 60 * 24)
        return new_submenu

    except Exception as e:
        print(f"Error in build_project: {e}")
        return []

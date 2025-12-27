from django.conf import settings
from django.core.cache import cache
from django.db.models import Exists, OuterRef
from apps.setup.models import Team

import copy
import json
import requests

from web_project.template_helpers.theme import TemplateHelper

API_BASE = settings.BASE_URL


def build_team():
    cache_key = "teams_submenu"
    submenu = cache.get(cache_key)
    if submenu is not None:
        print("BUILD_TEAM NOT EXECUTED")
        return submenu

    qs = (
        Team.objects.filter().distinct()
    )

    submenu = [{
        "url": "team",
        "name": "افزودن تیم",
        "slug": "team_list",
    }]

    for row in qs:
        team_id = row.id
        team_name = row.name

        submenu.append({
            "url": f"/team/{team_id}",
            "external": True,
            "name": team_name,
            "slug": "team_deteai"
        })

    cache.set(cache_key, submenu, 60 * 60 * 24)  # کش برای ۲۴ ساعت
    print("BUILD_TEAM EXECUTED")
    return submenu


menu_file = {
    "menu": [
        {
            "name": "پیشخوان",
            "icon": "menu-icon tf-icons ti ti-layout-dashboard",
            "slug": "dashboard",
            "submenu": [
                {
                    "url": "index",
                    "name": "نمای کلی",
                    "slug": "dashboard-analytics"
                }
            ]
        },
        {
            "name": "تیم ها",
            "icon": "menu-icon tf-icons ti ti-users-group",
            "slug": "teams",
            "submenu": []
        },
        {
            "name": "تنظیمات",
            "icon": "menu-icon tf-icons ti ti-settings",
            "slug": "setting",
            "submenu": [
                {
                    "url": "profile",
                    "name": "پروفایل",
                    "slug": "profile",
                },
                {
                    "url": "usersTable",
                    "name": "جدول کاربران",
                    "slug": "users_table"
                }
            ]
        },
        {
            "name": "پشتیبانی",
            "icon": "menu-icon tf-icons ti ti-help",
            "slug": "support",
            "submenu": [
                {
                    "url": "support",
                    "name": "ارسال تیکت",
                    "slug": "support"
                }
            ]
        }
    ]
}

"""
This is an entry and Bootstrap class for the theme level.
The init() function will be called in web_project/__init__.py
"""


class TemplateBootstrapLayoutVertical:

    @staticmethod
    def init(context):
        context.update(
            {
                "layout": "vertical",
                "content_navbar": True,
                "is_navbar": True,
                "is_menu": True,
                "is_footer": True,
                "navbar_detached": True,
            }
        )

        TemplateHelper.map_context(context)
        TemplateBootstrapLayoutVertical.init_menu_data(context)

        return context

    @staticmethod
    def init_menu_data(context):
        menu_data = copy.deepcopy(menu_file)

        for item in menu_data["menu"]:
            if item["slug"] == "teams":
                item["submenu"] = build_team()

        context.update({"menu_data": menu_data})

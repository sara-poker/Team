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

    submenu = []

    for row in qs:
        team_id = row.id
        team_name = row.name

        submenu.append({
            "url": f"/team/{team_id}",
            "external": True,
            "name": team_name,
            "slug": "team_deteai"
        })

    cache.set(cache_key, submenu, 60 * 60 * 24)
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
            "name": "مدیریت تیمینو",
            "icon": "menu-icon tf-icons ti ti-adjustments",
            "slug": "manager",
            "submenu": [
                {
                    "url": "team",
                    "name": "افزودن تیم",
                    "slug": "team_list",
                },
                {
                    "url": "projects",
                    "name": "افزودن پروژه",
                    "slug": "projects",
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


# @staticmethod
# def init_menu_data(context):
#     # دریافت اطلاعات کاربر از context
#     request = context.get('request')
#     user = request.user if request else None
#
#     menu_data = copy.deepcopy(menu_file)
#     filtered_menu = []
#
#     for item in menu_data["menu"]:
#         # ۱. محدودیت برای کل منوی "مدیریت تیمینو"
#         if item["slug"] == "manager":
#             if not user or not (user.role == 'manager' or user.role == 'admin'):
#                 continue  # اگر کاربر user معمولی بود، کل این بخش حذف می‌شود
#
#         # ۲. فیلتر کردن ساب‌منوها (برای نقش admin)
#         if item["slug"] == "manager" and user and user.role == 'admin':
#             # ادمین فقط باید "افزودن پروژه" رو ببینه
#             item["submenu"] = [sub for sub in item["submenu"] if sub["slug"] == "projects"]
#
#         # ۳. لود کردن تیم‌ها (کد قبلی خودت)
#         if item["slug"] == "teams":
#             item["submenu"] = build_team()
#
#         filtered_menu.append(item)
#
#     context.update({"menu_data": {"menu": filtered_menu}})

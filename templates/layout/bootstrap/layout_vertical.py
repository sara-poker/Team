import copy
from web_project.template_helpers.theme import TemplateHelper
from ..bootstrap.utils import *
from ..bootstrap.menu_dict import menu_user, menu_manager, menu_admin


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
        # از داخل شیء view که در context هست، request رو بیرون می‌کشیم
        view = context.get('view')
        request = getattr(view, 'request', None)

        user = request.user if request else None

        # حالا منطق قبلی رو ادامه می‌دیم
        if user and user.is_authenticated:
            if user.role == "manager":
                selected_menu = menu_manager
            elif user.role == "admin":
                selected_menu = menu_admin
            else:
                selected_menu = menu_user
        else:
            selected_menu = menu_user

        menu_data = copy.deepcopy(selected_menu)

        if "menu" in menu_data:
            for item in menu_data["menu"]:
                if item.get("slug") == "teams":
                    item["submenu"] = build_team()
                    break

        context.update({"menu_data": menu_data})

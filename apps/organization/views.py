from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from apps.organization.models import *

from web_project import TemplateLayout


class ProjectsView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        User = get_user_model()

        projects = Project.objects.all()
        for project in projects:
            project.progress = project.get_project_progress()

        teams = Team.objects.all()
        users = User.objects.all()

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['projects'] = projects
        context['teams'] = teams
        context['users'] = users
        return context

    def post(self, request, *args, **kwargs):

        if 'delete_team_id' in request.POST:
            team_id = request.POST.get('delete_team_id')
            try:
                Team.objects.get(id=team_id).delete()
                return redirect(f"{request.path}?alert_class=success_alert_mo&message=تیم با موفقیت حذف شد")
            except ProtectedError:
                return redirect(
                    f"{request.path}?alert_class=err_alert_mo&message=برای این تیم پروژه و تسک هایی تعریف شده است، برای حذف تیم ابتدا پروژه های آن را به سایر تیم ها منتقل کنید.")

        # اضافه کردن سرور جدید
        name = request.POST.get('team_name', '').strip()
        parent_team = request.POST.get('parent_team')

        if not name:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=لطفاً فیلد نام را پر کنید.")

        if Team.objects.filter(name=name).exists():
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=نام تیم تکراری است")

        if parent_team == 0 or parent_team == "0" or not parent_team:
            parent_team = None

        Team.objects.create(
            name=name,
            parent_id=parent_team,
        )

        return redirect(f"{request.path}?alert_class=success_alert_mo&message=تیم با موفقیت ثبت شد")

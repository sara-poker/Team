from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.shortcuts import redirect, get_object_or_404
from config.utils import *

from apps.organization.models import *
from web_project import TemplateLayout


class ProjectsView(StaffRequiredMixin,TemplateView):
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
        # context['role'] =
        return context

    def post(self, request, *args, **kwargs):

        if 'delete_project_id' in request.POST:
            project_id = request.POST.get('delete_project_id')
            try:
                Project.objects.get(id=project_id).delete()
                return redirect(f"{request.path}?alert_class=success_alert_mo&message=پروژه با موفقیت حذف شد")
            except ProtectedError:
                return redirect(
                    f"{request.path}?alert_class=err_alert_mo&message=برای این پروژه، تسک هایی تعریف شده است، برای حذف پروژه ابتدا تسک های آن را به سایر پروژه ها منتقل کنید."
                )

        projects = Project.objects.all()
        last_project = Project.objects.order_by('-id').first()
        if last_project:
            try:
                code = int(last_project.code) + 1
            except (ValueError, TypeError):
                code = 1001
        else:
            code = 1001


        title = request.POST.get('project_title', '').strip()
        teams_id = request.POST.getlist('teams_project', '')
        members_id = request.POST.getlist('member_project', '')
        description = request.POST.get('description', '')

        if not title:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=لطفاً عنوان پروژه را وارد کنید.")

        if not teams_id:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=حتما یک تیم را وارد کنید")

        # Create the project
        project = Project.objects.create(
            code=str(code),
            title=title,
            description=description,
            created_by=request.user
        )

        # Add teams to the project
        if teams_id:
            project.teams.set(teams_id)

        # Add members to the project
        if members_id:
            project.members.set(members_id)

        return redirect(f"{request.path}?alert_class=success_alert_mo&message=پروژه با موفقیت ثبت شد")

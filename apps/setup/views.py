from django.db.models import ProtectedError
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from web_project import TemplateLayout
from config.utils import *

from apps.setup.models import Team


class TeamView(ManagerOnlyMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        users = User.objects.all().exclude(id=self.request.user.id)
        teams = Team.objects.filter(members_teams=self.request.user)

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
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

        User = get_user_model()
        name = request.POST.get('team_name', '').strip()
        parent_team = request.POST.get('parent_team')
        members_id = request.POST.getlist('member_project', '')

        if not name:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=لطفاً فیلد نام را پر کنید.")

        if Team.objects.filter(name=name).exists():
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=نام تیم تکراری است")

        if parent_team == 0 or parent_team == "0" or not parent_team:
            parent_team = None

        team = Team.objects.create(
            name=name,
            parent_id=parent_team,
            created_by=request.user
        )

        members = User.objects.filter(id__in=members_id)

        team.members_teams.add(request.user)
        team.members_teams.add(*members)

        return redirect(f"{request.path}?alert_class=success_alert_mo&message=تیم با موفقیت ثبت شد")


class TeamDetail(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        team = get_object_or_404(Team, id=self.kwargs['pk'])

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['team'] = team
        return context


class ProfileView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        context['device_info_list'] = []
        context['network_info_list'] = []

        return context


class UserDetailView(StaffRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        user = User.objects.filter(id=self.kwargs['pk'])

        context['user'] = user[0]
        context['device_info_list'] = []
        context['network_info_list'] = []

        return context


class UsersTableView(StaffRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        users = User.objects.exclude(id=self.request.user.id).exclude(username="admin1")

        context['users'] = users
        return context

from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model

from web_project import TemplateLayout

from apps.setup.models import Team


class TeamView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        teams = Team.objects.all()

        context['teams'] = teams
        return context

class ProfileView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        context['device_info_list'] = []
        context['network_info_list'] = []

        return context


class UserDetailView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        user = User.objects.filter(id=self.kwargs['pk'])


        context['user'] = user[0]
        context['device_info_list'] = []
        context['network_info_list'] = []

        return context


class UsersTableView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        users = User.objects.exclude(id=self.request.user.id)

        context['users'] = users
        return context



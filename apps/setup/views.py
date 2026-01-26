from django.db.models import Count, Q, ProtectedError
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseForbidden

from web_project import TemplateLayout
from config.utils import *

from apps.setup.models import Team
from apps.organization.models import *


class TeamView(ManagerOnlyMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        users = User.objects.all().exclude(id=self.request.user.id).exclude(is_superuser=True)
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
                return redirect(
                    f"{request.path}?alert_class=success_alert_mo&message=تیم با موفقیت حذف شد"
                )


            except ValidationError:
                return redirect(
                    f"{request.path}?alert_class=err_alert_mo&message=برای این تیم پروژه‌هایی تعریف شده است. ابتدا پروژه‌ها را منتقل کنید."
                )
        User = get_user_model()
        name = request.POST.get('team_name', '').strip()
        parent_team = request.POST.get('parent_team')
        members_id = request.POST.getlist('member_project', '')

        superuser_ids = User.objects.filter(is_superuser=True).values_list('id', flat=True)
        members_id = list(
            set(map(str, members_id)) | set(map(str, superuser_ids))
        )

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

        User = get_user_model()
        user = self.request.user

        if user.role == 'manager':
            users = User.objects.all().exclude(is_superuser=True)
        else:
            users = []

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['team'] = team
        context['available_users'] = users
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
        users = User.objects.exclude(id=self.request.user.id).exclude(is_superuser=True)

        context['users'] = users
        return context


@login_required
def team_detail(request, team_id):
    """صفحه جزئیات تیم"""
    team = get_object_or_404(Team, id=team_id)

    # کاربرانی که عضو این تیم نیستند (برای افزودن)
    User = get_user_model()
    available_users = User.objects.exclude(
        id__in=team.members_teams.values_list('id', flat=True)
    ).exclude(is_superuser=True)

    context = {
        'team': team,
        'available_users': available_users,
    }
    return render(request, 'teams/team_detail.html', context)


@login_required
def team_projects_api(request, team_id):
    """API پروژه‌های تیم"""
    team = get_object_or_404(Team, id=team_id)
    projects = team.teams_projects.all()
    user = request.user

    if user.role == 'user':
        projects = projects.filter(members=user)

    data = []
    for project in projects:
        # دریافت اعضای پروژه (حداکثر 5 نفر)
        members_list = []
        all_members = project.members.all().exclude(is_superuser=True)

        for member in all_members[:5]:
            members_list.append({
                'id': member.id,
                'full_name': member.get_full_name() or member.username,
                'avatar': f'{member.username}.png'
            })

        data.append({
            'id': project.id,
            'title': project.title,
            'status': project.status,
            'progress': project.get_project_progress(),
            'members': members_list,
            'total_members': all_members.count(),
        })

    return JsonResponse({'data': data})


@login_required
def team_members_api(request, team_id):
    """API اعضای تیم"""
    team = get_object_or_404(Team, id=team_id)

    # تعداد تسک‌های هر عضو در پروژه‌های این تیم
    team_projects = team.teams_projects.all()

    members = team.members_teams.annotate(
        tasks_count=Count(
            'members_tasks',
            filter=Q(members_tasks__project__in=team_projects),
            distinct=True
        )
    ).exclude(is_superuser=True)

    # نمایش نقش‌ها به فارسی
    role_display = {
        'admin': 'سرپرست تیم',
        'manager': 'مدیر مجموعه',
        'user': 'کارشناس',
    }

    data = []
    for user in members:
        data.append({
            'id': user.id,
            'full_name': user.get_full_name() or user.username,
            'username': user.username,
            'role': getattr(user, 'role', 'user'),
            'role_display': role_display.get(getattr(user, 'role', 'user'), 'کاربر'),
            'tasks_count': user.tasks_count,
            'avatar': f'{user.username}.png'
        })

    return JsonResponse({'data': data})


@login_required
def add_team_member(request, team_id):
    """افزودن عضو به تیم"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    User = get_user_model()
    team = get_object_or_404(Team, id=team_id)

    # بررسی دسترسی
    if request.user.role not in ['admin', 'manager']:
        return HttpResponseForbidden('Access denied')

    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)

    user = get_object_or_404(User, id=user_id)

    # بررسی عضویت قبلی
    if team.members_teams.filter(id=user.id).exists():
        return JsonResponse({'error': 'User already member'}, status=400)

    team.members_teams.add(user)

    return JsonResponse({'status': 'ok', 'message': 'Member added successfully'})


@login_required
def remove_team_member(request, team_id, user_id):
    """حذف عضو از تیم"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    User = get_user_model()
    team = get_object_or_404(Team, id=team_id)

    # بررسی دسترسی
    if request.user.role not in ['admin', 'manager']:
        return HttpResponseForbidden('Access denied')

    user = get_object_or_404(User, id=user_id)

    team.members_teams.remove(user)

    return JsonResponse({'status': 'ok', 'message': 'Member removed successfully'})

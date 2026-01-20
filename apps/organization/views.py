from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError, Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.http import JsonResponse, HttpResponseForbidden

from django.contrib.auth.decorators import login_required

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from config.utils import *

from apps.organization.models import *
from apps.organization.serializers import *
from web_project import TemplateLayout

import jdatetime
from datetime import datetime
from django.utils import timezone


class ProjectsView(StaffRequiredMixin, TemplateView):
    from django.contrib.auth import get_user_model

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        User = get_user_model()

        user = self.request.user

        projects = Project.objects.filter(
            teams__members_teams=user
        ).distinct()

        for project in projects:
            project.progress = project.get_project_progress()

        teams = Team.objects.filter(members_teams=user).distinct()

        if user.role == 'manager':
            users = User.objects.all().exclude(is_superuser=True)

        elif user.role == 'admin':
            users = User.objects.filter(
                teams__in=teams
            ).exclude(role="manager").exclude(is_superuser=True).distinct()

        else:
            users = []

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['projects'] = projects
        context['teams'] = teams
        context['users'] = users

        return context

    def post(self, request, *args, **kwargs):
        User = get_user_model()

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
        members_id = request.POST.getlist('member_project', [])
        description = request.POST.get('description', '')

        superuser_ids = User.objects.filter(is_superuser=True).values_list('id', flat=True)
        members_id = list(
            set(map(str, members_id)) | set(map(str, superuser_ids))
        )

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


class ProjectDetail(TemplateView):
    template_name = 'project/detail.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        User = get_user_model()
        user = self.request.user

        teams = Team.objects.filter(members_teams=user).distinct()

        if user.role == 'manager':
            users = User.objects.all().exclude(is_superuser=True)

        elif user.role == 'admin':
            users = User.objects.filter(
                teams__in=teams
            ).exclude(role="manager").exclude(is_superuser=True).distinct()

        else:
            users = []

        project = get_object_or_404(Project, id=self.kwargs['pk'])

        tasks = project.task_set.all()

        context.update({
            'project': project,
            'progress': project.get_project_progress(),
            'total_tasks': tasks.count(),
            'task_not_started': tasks.filter(status='not_started').count(),
            'task_in_progress': tasks.filter(status='in_progress').count(),
            'task_reviewing': tasks.filter(status='reviewing').count(),
            'task_completed': tasks.filter(status='completed').count(),
            'users': users
        })

        return context


class ProjectChangeStatusView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        status_flow = ['not_started', 'in_progress', 'completed']

        if project.status == 'completed':
            project.status = 'in_progress'
            project.end_date = None
        else:
            current_index = status_flow.index(project.status)
            if project.status == 'not_started':
                project.start_date = timezone.now().date()
            elif project.status == 'in_progress':
                project.end_date = timezone.now().date()

            if current_index < len(status_flow) - 1:
                project.status = status_flow[current_index + 1]

        project.save()
        return redirect(reverse('projects_detail', args=[pk]))


class TasksProjectDetail(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        project = get_object_or_404(Project, id=self.kwargs['pk'])
        qu_pa = self.request.GET.get('status', 'not_started')

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['project'] = project
        context['qu_pa'] = qu_pa
        return context

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, id=self.kwargs['pk'])

        title = request.POST.get('title', '').strip()
        weight = request.POST.get('weight', 1)

        user = self.request.user

        if not title:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=لطفاً عنوان تسک را وارد کنید")

        try:
            new_task = Task.objects.create(
                title=title,
                weight=weight,
                project=project,
                created_by=request.user,
                status='not_started',
                percent=0.0
            )

            if user.role == 'user':
                new_task.assignees.add(user)

            success_url = reverse('tasks_detail', kwargs={'pk': project.id, 'task_id': new_task.id})
            return redirect(f"{success_url}")

        except Exception as e:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=خطایی در ثبت تسک رخ داد")


class TasksDetail(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        project = get_object_or_404(Project, id=self.kwargs['pk'])
        task = get_object_or_404(Task, id=self.kwargs['task_id'])

        qu_pa = self.request.GET.get('status', 'not_started')

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['project'] = project
        context['qu_pa'] = qu_pa
        context['task'] = task
        context['user_role'] = self.request.user.role

        context['is_assignee'] = self.request.user.is_superuser or (self.request.user in task.assignees.all())
        context['can_edit'] = (
            self.request.user.role != "user" or
            self.request.user in task.assignees.all() or
            self.request.user.is_superuser
        )

        return context

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, id=self.kwargs['pk'])

        if 'change_status' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, project=project)

            is_assignee = request.user in task.assignees.all()
            if request.user.role == "user" and not is_assignee:
                return redirect(f"{request.path}?alert_class=err_alert_mo&message=شما دسترسی ندارید")

            new_status = request.POST.get('change_status')
            if new_status:
                if request.user.role == "user" and new_status == "completed":
                    return redirect(
                        f"{request.path}?alert_class=err_alert_mo&message=فقط مدیر می‌تواند تسک را تکمیل کند")

                task.status = new_status

                if new_status == "in_progress":
                    task.start_date = timezone.now().date()
                elif new_status == "reviewing":
                    task.end_date = timezone.now().date()

                task.save()

            qu_pa = f"?status={task.status}" if task.status != "not_started" else ""
            return redirect(f"{request.path}{qu_pa}")

        if 'delete_task' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, project=project)

            if request.user.role == "user" and task.created_by != request.user:
                return redirect(f"{request.path}?alert_class=err_alert_mo&message=شما اجازه حذف این تسک را ندارید")

            task.delete()
            success_delete_url = reverse('tasks_project', kwargs={'pk': project.id})
            return redirect(f"{success_delete_url}?alert_class=success_alert_mo&message=تسک با موفقیت حذف شد")

        if 'update_task' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, project=project)

            is_assignee = request.user in task.assignees.all()
            is_manager_or_admin = request.user.role != "user"

            if not is_assignee and not is_manager_or_admin:
                return redirect(f"{request.path}?alert_class=err_alert_mo&message=شما دسترسی ویرایش ندارید")

            if is_manager_or_admin:
                new_status_val = request.POST.get('status')
                if new_status_val:
                    task.status = new_status_val

            description_val = request.POST.get('description')
            if description_val is not None:
                task.description = description_val

            percent_val = request.POST.get('percent')
            if percent_val:
                task.percent = float(percent_val)

            if is_manager_or_admin:
                weight_val = request.POST.get('weight')
                if weight_val:
                    task.weight = int(weight_val)

            deadline_shamsi = request.POST.get('deadline')
            if deadline_shamsi:
                try:
                    date_parts = deadline_shamsi.replace('/', '-').split('-')
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    jalali_date = jdatetime.date(year, month, day)
                    task.deadline = jalali_date.togregorian()
                except (ValueError, IndexError):
                    pass

            task.save()

            if is_manager_or_admin:
                assignees_ids = request.POST.getlist('assignees')
                if assignees_ids:
                    task.assignees.set(assignees_ids)
                else:
                    task.assignees.clear()

            qu_pa = f"?status={task.status}" if task.status != "not_started" else ""
            return redirect(
                f"{request.path}?alert_class=success_alert_mo&message=تسک بروزرسانی شد{qu_pa.replace('?', '&') if qu_pa else ''}")

        title = request.POST.get('title', '').strip()
        weight = request.POST.get('weight', 1)

        if not title:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=عنوان نمی‌تواند خالی باشد")

        new_task = Task.objects.create(
            title=title,
            weight=int(weight),
            project=project,
            created_by=request.user,

        )

        if request.user.role == "user":
            new_task.assignees.add(request.user)

        success_url = reverse('tasks_detail', kwargs={'pk': project.id, 'task_id': new_task.id})
        return redirect(f"{success_url}?status=not_started&alert_class=success_alert_mo&message=تسک ایجاد شد")


class GetAllTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        queryset = Task.objects.filter(project_id=project_id)

        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        tasks = list(queryset)

        tasks.sort(
            key=lambda task: task.get_task_priority(),
            reverse=True
        )

        serializer = GetAllTaskAPISerializer(
            tasks,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


@login_required
def project_members_api(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    members = (
        project.members
        .annotate(
            tasks_count=Count(
                'members_tasks',
                filter=Q(members_tasks__project=project),
                distinct=True
            )
        )
    ).exclude(is_superuser=True)

    data = []
    for user in members:
        data.append({
            'id': user.id,
            'full_name': f'{user.first_name} {user.last_name}'.strip(),
            'username': user.username,
            'role': getattr(user, 'role', ''),
            'tasks_count': user.tasks_count,
            'avatar': f'{user.username}.png'
        })

    return JsonResponse({'data': data})


@login_required
def remove_project_member(request, project_id, user_id):
    User = get_user_model()
    project = get_object_or_404(Project, id=project_id)

    if not can_manage_project_members(request.user, project):
        return HttpResponseForbidden('Access denied')

    user = get_object_or_404(User, id=user_id)

    project.members.remove(user)

    return JsonResponse({'status': 'ok'})


@login_required
def add_project_member(request, project_id):
    User = get_user_model()
    project = get_object_or_404(Project, id=project_id)

    if not can_manage_project_members(request.user, project):
        return HttpResponseForbidden('Access denied')

    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, id=user_id)

    project.members.add(user)

    return JsonResponse({'status': 'ok'})

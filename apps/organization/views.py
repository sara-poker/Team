from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.utils import *

from apps.organization.models import *
from apps.organization.serializers import *
from web_project import TemplateLayout

import jdatetime
from datetime import datetime


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
            users = User.objects.all().exclude(id=self.request.user.id).exclude(username="admin1")

        elif user.role == 'admin':
            users = User.objects.filter(
                teams__in=teams
            ).exclude(id=self.request.user.id).exclude(username="admin1").distinct()

        else:
            users = User.objects.filter(id=user.id)

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['projects'] = projects
        context['teams'] = teams
        context['users'] = users

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


class ProjectDetail(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        project = get_object_or_404(Project, id=self.kwargs['pk'])

        context['class_notification'] = self.request.GET.get('alert_class', 'none_alert_mo')
        context['message'] = self.request.GET.get('message', '')
        context['project'] = project
        return context


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
        return context

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, id=self.kwargs['pk'])

        if 'change_status' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, project=project)

            new_status = request.POST.get('change_status')
            task.status = new_status

            if new_status == "in_progress":
                task.start_date = timezone.now().date()
            elif new_status == "reviewing":
                task.end_date = timezone.now().date()

            task.save()

            if task.status != "not_started":
                qu_pa = f"?status={task.status}"
            else:
                qu_pa = ""
            return redirect(f"{request.path}{qu_pa}")

        if 'delete_task' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, project=project)
            task.delete()
            success_delete_url = reverse('tasks_project', kwargs={'pk': project.id})
            return redirect(f"{success_delete_url}")

        if 'update_task' in request.POST:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, project=project)

            task.title = request.POST.get('title').strip()
            task.status = request.POST.get('status')
            task.description = request.POST.get('description')
            task.percent = float(request.POST.get('percent', 0))
            task.weight = int(request.POST.get('weight', 1))

            deadline_shamsi = request.POST.get('deadline')

            if deadline_shamsi:
                try:
                    date_parts = deadline_shamsi.replace('/', '-').split('-')
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])

                    jalali_date = jdatetime.date(year, month, day)

                    deadline = jalali_date.togregorian()

                    task.deadline = deadline
                except (ValueError, IndexError):
                    pass

            task.save()

            assignees_ids = request.POST.getlist('assignees')
            task.assignees.set(assignees_ids) if assignees_ids else task.assignees.clear()

            if task.status != "not_started":
                qu_pa = f"?status={task.status}"
            else:
                qu_pa = ""

            return redirect(f"{request.path}{qu_pa}")

        title = request.POST.get('title', '').strip()
        weight = request.POST.get('weight', 1)

        if not title:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=عنوان نمی‌تواند خالی باشد")

        new_task = Task.objects.create(
            title=title,
            weight=int(weight),
            project=project,
            created_by=request.user
        )

        success_url = reverse('tasks_detail', kwargs={'pk': project.id, 'task_id': new_task.id})
        return redirect(f"{success_url}?status=not_started&alert_class=success_alert_mo&message=تسک ایجاد شد")


class GetAllTaskView(APIView):
    permission_classes = [AllowAny]

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

        serializer = GetAllTaskAPISerializer(tasks, many=True)
        return Response(serializer.data)

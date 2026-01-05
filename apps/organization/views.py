from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

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
            users = User.objects.all().exclude(id=self.request.user.id).exclude(is_superuser = True)

        elif user.role == 'admin':
            users = User.objects.filter(
                teams__in=teams
            ).exclude(id=self.request.user.id).exclude(is_superuser = True).distinct()

        else:
            users = User.objects.filter(id=user.id)

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


from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
import jdatetime


class TasksDetail(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # فرض بر این است که TemplateLayout.init خروجی کانتکست را اصلاح می‌کند
        context = TemplateLayout.init(self, context)

        project = get_object_or_404(Project, id=self.kwargs['pk'])
        task = get_object_or_404(Task, id=self.kwargs['task_id'])

        qu_pa = self.request.GET.get('status', 'not_started')

        # بررسی دسترسی برای نمایش در فرانت
        is_assignee = task.assignees.filter(id=self.request.user.id).exists()
        can_edit = True
        if self.request.user.role == "user" and not is_assignee:
            can_edit = False

        context.update({
            'class_notification': self.request.GET.get('alert_class', 'none_alert_mo'),
            'message': self.request.GET.get('message', ''),
            'project': project,
            'qu_pa': qu_pa,
            'task': task,
            'can_edit': can_edit,
        })
        return context

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, id=self.kwargs['pk'])
        task_id = request.POST.get('task_id')
        task = get_object_or_404(Task, id=task_id, project=project)

        # ۱. بررسی سطح دسترسی امنیتی
        is_assignee = task.assignees.filter(id=request.user.id).exists()
        if request.user.role == "user" and not is_assignee:
            return redirect(f"{request.path}?alert_class=err_alert_mo&message=شما دسترسی ویرایش این تسک را ندارید")

        # ۲. عملیات تغییر وضعیت سریع
        if 'change_status' in request.POST:
            new_status = request.POST.get('change_status')
            if new_status:
                task.status = new_status
                if new_status == "in_progress":
                    task.start_date = timezone.now().date()
                elif new_status == "reviewing":
                    task.end_date = timezone.now().date()
                task.save()

            qu_pa = f"?status={task.status}" if task.status != "not_started" else ""
            return redirect(f"{request.path}{qu_pa}")

        # ۳. حذف تسک
        if 'delete_task' in request.POST and request.user.role != "user":
            task.delete()
            return redirect(reverse('tasks_project', kwargs={'pk': project.id}))

        # ۴. به‌روزرسانی کلی (جلوگیری از ارور NotNullViolation)
        if 'update_task' in request.POST:
            # فقط اگر مقدار در POST بود تغییر بده، در غیر این صورت مقدار قبلی رو نگه دار
            task.status = request.POST.get('status') or task.status
            task.description = request.POST.get('description') or task.description

            if request.POST.get('percent'):
                task.percent = float(request.POST.get('percent'))

            if request.POST.get('weight'):
                task.weight = int(request.POST.get('weight'))

            deadline_shamsi = request.POST.get('deadline')
            if deadline_shamsi:
                try:
                    date_parts = deadline_shamsi.replace('/', '-').split('-')
                    jalali_date = jdatetime.date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                    task.deadline = jalali_date.togregorian()
                except (ValueError, IndexError):
                    pass

            task.save()

            # آپدیت لیست مسئولین (فقط برای مدیران یا در صورت ارسال فیلد)
            assignees_ids = request.POST.getlist('assignees')
            if assignees_ids:
                task.assignees.set(assignees_ids)
            elif request.user.role != "user":
                # اگر مدیر بود و لیست خالی فرستاد، پاک کن. اگر کاربر عادی بود و لیست نیومد، دست نزن.
                task.assignees.clear()

            qu_pa = f"?status={task.status}" if task.status != "not_started" else ""
            return redirect(f"{request.path}{qu_pa}")

        return redirect(request.path)


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

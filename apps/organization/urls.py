from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path(
        "projects/",
        login_required(ProjectsView.as_view(template_name="projects.html")),
        name="projects",
    ),
    path(
        "projects/<int:pk>",
        login_required(ProjectDetail.as_view(template_name="projects_detail.html")),
        name="projects_detail",
    ),
    path('projects/<int:pk>/change-status/',
         login_required(ProjectChangeStatusView.as_view()),
         name='project_change_status'),

    path(
        "projects/<int:pk>/tasks",
        login_required(TasksProjectDetail.as_view(template_name="tasks_project.html")),
        name="tasks_project",
    ),
    path(
        "projects/<int:pk>/tasks/<int:task_id>/",
        login_required(TasksDetail.as_view(template_name="tasks_detail.html")),
        name="tasks_detail",
    ),
    path(
        "api/getAllTask/<int:project_id>",
        GetAllTaskView.as_view(),
        name="get_all_tast"
    ),
    path(
        'projects/<int:project_id>/members/',
        project_members_api,
        name='project_members_api'
    ),
    path(
        'projects/<int:project_id>/members/add/',
        add_project_member,
        name='add_project_member'
    ),
    path(
        'projects/<int:project_id>/members/remove/<int:user_id>/',
        remove_project_member,
        name='remove_project_member'
    )
]

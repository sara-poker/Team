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
    path(
        "projects/<int:pk>/tasks",
        login_required(TasksProjectDetail.as_view(template_name="tasks_project.html")),
        name="tasks_project",
    )
]

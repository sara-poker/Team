from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path(
        "projects/",
        login_required(ProjectsView.as_view(template_name="projects.html")),
        name="projects",
    ),
]

from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path(
        "team/",
        login_required(TeamView.as_view(template_name="team.html")),
        name="team",
    ),
    path(
        "team/<int:pk>",
        login_required(TeamDetail.as_view(template_name="team_detail.html")),
        name="team_detail",
    ),
    path(
        "setup/profile",
        login_required(ProfileView.as_view(template_name="profile.html")),
        name="profile",
    ),
    path(
        "setup/users/table",
        login_required(UsersTableView.as_view(template_name="users_table.html")),
        name="usersTable",
    ),
    path(
        "setup/user/detail/<int:pk>",
        login_required(UserDetailView.as_view(template_name="user_detail.html")),
        name="usersDetail",
    )
]

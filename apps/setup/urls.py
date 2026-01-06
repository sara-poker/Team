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
    ),
    path(
        'teams/<int:team_id>/projects/',
        team_projects_api,
        name='team_projects_api'
    ),
    path(
        'teams/<int:team_id>/members/',
        team_members_api,
        name='team_members_api'
    ),
    path(
        'teams/<int:team_id>/members/add/',
        add_team_member,
        name='add_team_member'
    ),
    path(
        'teams/<int:team_id>/members/remove/<int:user_id>/'
        , remove_team_member,
        name='remove_team_member'
    ),
]

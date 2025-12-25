from django.views.generic import (TemplateView)
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Avg, Count, Q
from django.shortcuts import redirect, get_object_or_404

from persiantools.jdatetime import JalaliDate

from web_project import TemplateLayout


from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
class ReportDashboardsView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context


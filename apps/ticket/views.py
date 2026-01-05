from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect

from apps.ticket.models import *

from web_project import TemplateLayout

import pandas as pd
import jdatetime




def convert_month(month):
    if month == "01":
        return "فروردین"
    if month == "02":
        return "اردیبهشت"
    if month == "03":
        return "خرداد"
    if month == "04":
        return "تیر"
    if month == "05":
        return "مرداد"
    if month == "06":
        return "شهریور"
    if month == "07":
        return "مهر"
    if month == "08":
        return "آبان"
    if month == "09":
        return "آذر"
    if month == "10":
        return "دی"
    if month == "11":
        return "بهمن"
    if month == "12":
        return "اسفند"


def convert_date(date):
    date = str(date)
    year = date[:4]
    month = date[4:6]
    day = date[6:8]
    return year + "/" + month + "/" + day


class StaffRequiredMixin(AccessMixin):
    redirect_url = '/ticket/support'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin2(AccessMixin):
    redirect_url = '/ticket'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin3(AccessMixin):
    redirect_url = '/report'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)



class SupportView(StaffRequiredMixin, TemplateView):
    template_name = "all_ticket.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        User = get_user_model()
        all_users = User.objects.filter(is_staff=False)

        context['users'] = all_users
        return context


class SupportViewById(StaffRequiredMixin, TemplateView):
    template_name = "support_by_id.html"  # نام فایل قالب خود را تنظیم کنید

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        User = get_user_model()
        all_users = User.objects.filter(is_staff=False)
        my_info = all_users.filter(pk=self.kwargs['pk'])

        messages = Message.objects.filter(user=self.kwargs['pk'])

        context['users'] = all_users
        context['my_info'] = my_info[0]
        context['messages'] = messages
        return context

    def post(self, request, *args, **kwargs):
        text = request.POST.get('text')
        user_id = self.kwargs['pk']

        if text:
            Message.objects.create(
                text=text,
                user_id=user_id,
                support_send=True,
                seen=False,
            )

        return redirect(request.path)


class UserView(StaffRequiredMixin2, TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        messages = Message.objects.filter(user=self.request.user)

        context['messages'] = messages
        return context

    def post(self, request, *args, **kwargs):
        text = request.POST.get('text')
        user_id = self.request.user.id

        if text:
            Message.objects.create(
                text=text,
                user_id=user_id,
                support_send=False,
                seen=False,
            )

        return redirect(request.path)


class NotificationView(TemplateView):
    def get_context_data(self, **kwargs):
        # دریافت context اصلی
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # دریافت تمام اعلان‌های کاربر فعلی
        notifications = Notification.objects.filter(user=self.request.user).order_by('-created_at')

        # اضافه کردن اعلان‌ها به context
        context['notifications'] = notifications
        return context


class UpdateNotificationStatusView(View):
    def post(self, request, *args, **kwargs):
        # بروزرسانی وضعیت اعلان‌ها برای کاربر فعلی
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})

from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


class ManagerOnlyMixin(AccessMixin):
    redirect_url = '/report/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "manager":
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(AccessMixin):
    redirect_url = '/report/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ["manager", "admin"]:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class AdminOnlyMixin(AccessMixin):
    redirect_url = '/report/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "admin":
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class UserOnlyMixin(AccessMixin):
    redirect_url = '/report/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "user":
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)

from rest_framework.serializers import BaseSerializer
from rest_framework import serializers

from apps.organization.models import *

class GetAllTaskAPISerializer(serializers.ModelSerializer):
    priority = serializers.SerializerMethodField()
    time_difference = serializers.SerializerMethodField()
    is_my_task = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'weight',
            'priority',
            'time_difference',
            'is_my_task',
        ]

    def get_priority(self, obj):
        return obj.get_task_priority()

    def get_time_difference(self, obj):
        diff = obj.get_time_difference()
        if diff is None:
            return None

        days = diff.days
        if days > 0:
            return days
        elif days < 0:
            return days
        return 0

    def get_is_my_task(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return obj.assignees.filter(id=request.user.id).exists()


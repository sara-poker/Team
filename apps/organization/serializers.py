from rest_framework.serializers import BaseSerializer
from rest_framework import serializers

from apps.organization.models import *

class GetAllTaskAPISerializer(serializers.ModelSerializer):
    priority = serializers.SerializerMethodField()
    time_difference = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'weight',
            'priority',
            'time_difference',
        ]

    def get_priority(self, obj):
        return obj.get_task_priority()

    def get_time_difference(self, obj):
        diff = obj.get_time_difference()
        if diff is None:
            return None

        days = diff.days
        if days > 0:
            # return f"{days} روز گذشته"
            return days
        elif days < 0:
            # return f"{abs(days)} روز مانده"
            return days
        return 0


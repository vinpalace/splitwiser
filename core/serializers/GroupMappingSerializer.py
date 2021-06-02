from rest_framework import serializers
from core.models import GroupMapping


class GroupMappingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupMapping
        fields = '__all__'

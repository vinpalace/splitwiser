from django.contrib.auth.models import User
from core.serializers.GroupMappingSerializer import GroupMappingSerializer
from core.serializers.GroupSerializer import GroupSerializer
from core.serializers.UserSerializer import UserSerializer
from rest_framework import viewsets
from core.models import Group, GroupMapping
from rest_framework .response import Response
from rest_framework.decorators import action
from rest_framework import status


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @action(detail=True, methods=['post'])
    def add_user_to_group(self, request, pk=None):
        request_params = request.data
        group = self.get_object()
        user = User.objects.get(id=request_params['user_id'])

        GroupMapping.objects.create(
            user=user,
            group=group
        )
        return Response(
            {'status': status.HTTP_200_OK}
        )

    @action(detail=True, methods=['post'])
    def remove_user_from_group(self, request, pk=None):
        try:
            request_params = request.data
            group = self.get_object()
            user = User.objects.get(id=request_params['user_id'])

            GroupMapping.objects.filter(user=user, group=group).delete()
            return Response(
                {'status': status.HTTP_200_OK}
            )
        except Exception:
            return Response(
                {'status': status.HTTP_400_BAD_REQUEST}
            )

    @action(detail=True, methods=['GET'])
    def get_users_in_group(self, request, pk=None):
        mapping_list = GroupMapping.objects.filter(group=self.get_object())
        users = [mapping.user for mapping in mapping_list]

        serialized_users = UserSerializer(
            users, context={'request': request}, many=True)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'users': serialized_users.data
            }
        )

from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions

from rest_framework import serializers, viewsets

from main.models import (
        Cluster,
        Gres,
        Scheduler,
        Job, 
        CVTUser,
        Group,
        UserGroupLink,
        GresClusterLink,
        GresGroupLink,
        GresUserGroupLinkLink,
        GresCVTUserLink
)


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = '__all__'


class GresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gres
        fields = '__all__'


class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.user.username')
    group = serializers.CharField(source='group.name')

    class Meta:
        model = Job
        exclude = ('id', 'cluster')

 
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class CVTUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVTUser
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class UserGroupLinkSerializer(serializers.ModelSerializer):
    user = CVTUserSerializer(read_only=True)
    group = GroupSerializer(read_only=True)

    class Meta:
        model = UserGroupLink
        fields = '__all__'


class GresClusterLinkSerializer(serializers.ModelSerializer):
    cluster = ClusterSerializer(read_only=True)
    gres = GresSerializer(read_only=True)

    class Meta:
        model = GresClusterLink
        fields = '__all__'


class GresGroupLinkSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    gres = GresSerializer(read_only=True)

    class Meta:
        model = GresGroupLink
        fields = '__all__'


class GresUserGroupLinkLinkSerializer(serializers.ModelSerializer):
    ugl = UserGroupLinkSerializer(read_only=True)
    gres = GresSerializer(read_only=True)

    class Meta:
        model = GresUserGroupLinkLink
        fields = '__all__'


class GresCVTUserLinkSerializer(serializers.ModelSerializer):
    user = CVTUserSerializer(read_only=True)
    gres = GresSerializer(read_only=True)

    class Meta:
        model = GresCVTUserLink
        fields = '__all__'


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    http_method_names = ['get', 'head']


class GresViewSet(viewsets.ModelViewSet):
    queryset = Gres.objects.all()
    serializer_class = GresSerializer
    http_method_names = ['get', 'head']


class SchedulerViewSet(viewsets.ModelViewSet):
    queryset = Scheduler.objects.all()
    serializer_class = SchedulerSerializer
    http_method_names = ['get', 'head']


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    http_method_names = ['get', 'head']
    permission_classes = (IsAuthenticated,)


class CVTUserViewSet(viewsets.ModelViewSet):
    queryset = CVTUser.objects.all()
    serializer_class = CVTUserSerializer
    http_method_names = ['get', 'head']
    permission_classes = (IsAuthenticated,)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'head']
    permission_classes = (IsAuthenticated,)


class UserGroupLinkViewSet(viewsets.ModelViewSet):
    queryset = UserGroupLink.objects.all()
    serializer_class = UserGroupLinkSerializer
    http_method_names = ['get', 'head']
    permission_classes = (IsAuthenticated,)


class GresClusterLinkViewSet(viewsets.ModelViewSet):
    queryset = GresClusterLink.objects.all()
    serializer_class = GresClusterLinkSerializer
    http_method_names = ['get', 'head']


class GresGroupLinkViewSet(viewsets.ModelViewSet):
    queryset = GresGroupLink.objects.all()
    serializer_class = GresGroupLinkSerializer
    http_method_names = ['get', 'head']
    permission_classes = (IsAuthenticated,)


class GresUserGroupLinkLinkViewSet(viewsets.ModelViewSet):
    queryset = GresUserGroupLinkLink.objects.all()
    serializer_class = GresUserGroupLinkLinkSerializer
    http_method_names = ['get', 'head']
    permission_classes = (IsAuthenticated,)


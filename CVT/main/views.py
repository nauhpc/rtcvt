from CVT.CVTConfig import UI_COLORCODING
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from functools import reduce
from rest_framework import permissions, generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from main.models import (
    CVTUser,
    Group,
    Gres,
    Job,
    Cluster,
    UserGroupLink,
    CVTUser,
    GresClusterLink,
    GresGroupLink,
    GresUserGroupLinkLink,
    GresCVTUserLink,
)
from main.serializers import (
        JobSerializer,
        GroupSerializer,
        ClusterSerializer,
        GresSerializer,
        UserSerializer,
        UserGroupLinkSerializer,
        GresClusterLinkSerializer,
        GresGroupLinkSerializer,
        GresUserGroupLinkLinkSerializer,
        GresCVTUserLinkSerializer,
)


@api_view(['GET'])
@permission_classes((AllowAny,))
def active_user(request):
    user = request.user
    if user is None or user.username == "":
        # TODO: Need to handle this better. If a user.username == "" that means they're AnonymousUser, so this shouldn't be an exception probably, but does need to return something helpful for the frontend to know that they aren't logged in
        raise Exception("user does not exist")
    else:
        data = {"username": user.username}
    return Response(data)

@api_view(['GET']) 
@permission_classes((AllowAny,)) 
def jobColorCoding(request):
    return Response(UI_COLORCODING) 

# API view for cluster stats
class ClusterUsageList(generics.ListAPIView):
    serializer_class = ClusterSerializer

    def get_queryset(self):
        queryset = Cluster.objects.all()
        cluster_name = self.request.query_params.get('cluster', None)
        if cluster_name is not None:
            queryset = queryset.filter(name=cluster_name)
        return queryset

# API view for jobs
class JobList(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Job.objects.all()
        #uid = self.kwargs['uid']
        try:
            user = self.request.user
            cvt_user = CVTUser.objects.get(user=user)
            queryset = queryset.filter(user=cvt_user)
        except ObjectDoesNotExist:
            # TODO: figure out the appropriate way to handle this...what should be returned on failure?
            raise Exception("user does not exist")
        cluster_name = self.request.query_params.get('cluster', None)
        if cluster_name is not None:
            queryset = queryset.filter(user=cvt_user, cluster__name=cluster_name)
        return queryset

class GresList(generics.ListAPIView):

    def get_serializer_class(self):
        user = self.request.query_params.get('user', None)
        group = self.request.query_params.get('group', None)
        if group is not None and user is not None:
            return GresUserGroupLinkLinkSerializer
        elif group is not None:
            return GresGroupLinkSerializer
        elif user is not None:
            return GresCVTUserLinkSerializer
        else:
            return GresClusterLinkSerializer

    def get_queryset(self):
        # TODO: This whole method should probably be refactored
        self.serializer_class = self.get_serializer_class()

        if self.serializer_class == GresUserGroupLinkLinkSerializer:
            query_model = GresUserGroupLinkLink
        elif self.serializer_class == GresGroupLinkSerializer:
            query_model = GresGroupLink
        elif self.serializer_class == GresCVTUserLinkSerializer:
            query_model = GresCVTUserLink
        elif self.serializer_class == GresClusterLinkSerializer:
            query_model = GresClusterLink
        else:
            raise Exception("serializer class not found")

        cluster_name = self.kwargs['cluster']
        if cluster_name is None:
            raise Exception("cluster must be specified in url")
        else:
            try:
                cluster = Cluster.objects.get(name=cluster_name)
            except ObjectDoesNotExist:
                raise Exception("cluster does not exist")
            groupname = self.request.query_params.get('group', None)
            if query_model == GresUserGroupLinkLink:
                # TODO: maybe try/except here?
                group = Group.objects.get(name=groupname, cluster=cluster)
                user = CVTUser.objects.get(user__username=username)
                ugl = UserGroupLink.objects.get(user=user, group=group)
                queryset = query_model.objects.filter(ugl=ugl)
            elif query_model == GresGroupLink:
                group = Group.objects.get(name=groupname, cluster=cluster)
                queryset = query_model.objects.filter(group=group)
            elif query_model == GresCVTUserLink:
                user = CVTUser.objects.get(user=self.request.user)
                queryset = query_model.objects.filter(user=user)
            else:
                queryset = query_model.objects.filter(cluster=cluster)

        return queryset


class GroupJobList(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Job.objects.all()
        cluster_name = self.request.query_params.get('cluster', None)
        if self.kwargs['group'] == 'All':
            try:
                user = CVTUser.objects.get(user=self.request.user)
            except:
                raise Exception("User does not exist")
            queryset = Job.objects.filter(reduce(lambda x, y: x | y, [Q(group=g) for g in user.groups.all()]))
        else:
            try:
                queryset = queryset.filter(group__name=self.kwargs['group'])
            except ObjectDoesNotExist:
                raise Exception("No such group")
            except Exception as e:
                print(e)

        if cluster_name is not None:
            queryset = queryset.filter(cluster__name=cluster_name)
        return queryset


class UserGroupList(generics.ListAPIView):
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            user = CVTUser.objects.get(user=self.request.user)
        except:
            raise Exception("User does not exist")
        return user.groups.all()

class UserGroupLinkList(generics.ListAPIView):
    serializer_class = UserGroupLinkSerializer

    def get_queryset(self):
        queryset = UserGroupLink.objects.all()

        try:
            user = CVTUser.objects.get(user=self.request.user)
        except:
            raise Exception("User or Group does not exist")
        try:
            group = Group.objects.get(name=self.kwargs['group'], cluster__name=self.kwargs['cluster'])
        except:
            raise Exception("No such group")

        queryset = queryset.filter(user=user, group=group)

        return queryset

def test(request):
    html = "<html><body>Hello %s</body></html>" % request.user.username
    return HttpResponse(html)

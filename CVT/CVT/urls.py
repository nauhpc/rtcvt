"""cvt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.contrib import admin
from rest_framework import routers
from django_cas_ng import views as cas

from main.serializers import (
    ClusterViewSet,
    GresViewSet,
    GresClusterLinkViewSet,
    GresGroupLinkViewSet,
    GresUserGroupLinkLinkViewSet,
    SchedulerViewSet,
    JobViewSet,
    CVTUserViewSet,
    GroupViewSet,
    UserGroupLinkViewSet
)
from main.views import (
    JobList, 
    ClusterUsageList, 
    test, 
    active_user, 
    GresList, 
    GroupJobList, 
    UserGroupList,
    UserGroupLinkList, 
    jobColorCoding
)

router = routers.DefaultRouter()
router.register(r'clusters', ClusterViewSet)
router.register(r'gres', GresViewSet)
router.register(r'grescluster', GresClusterLinkViewSet)
router.register(r'gresgroup', GresGroupLinkViewSet)
router.register(r'gresugl', GresUserGroupLinkLinkViewSet)
router.register(r'schedulers', SchedulerViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'users', CVTUserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'user_group_links', UserGroupLinkViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^test/$', test, name="test_view"), 
    url(r'^accounts/login$', cas.login, name="login"),
    url(r'^accounts/logout$', cas.logout, name="logout"),
    url(r'^accounts/callback$', cas.callback, name='cas_ng_proxy_callback'),

    # rest api
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/getjobs/$', JobList.as_view(), name="get_jobs"),
    url(r'^api/getusage/$', ClusterUsageList.as_view(), name="get_usage"),
    url(r'^api/getgres/(?P<cluster>.+)/$', GresList.as_view(), name="get_gres"),
    url(r'^api/getgroupjobs/(?P<group>.+)/$', GroupJobList.as_view(), name='get_groupjob'),
    url(r'^api/getugl/(?P<cluster>.+)/(?P<group>.+)/$', UserGroupLinkList.as_view(), name="get_usergrouplink"),
    url(r'^api/getusergroups/$', UserGroupList.as_view(), name="get_usergroups"),
    url(r'^api/activeuser/$', active_user, name='current_user_view'),
    url(r'^api/jobcolorcoding/$', jobColorCoding, name='UICOLORCODING'),
]

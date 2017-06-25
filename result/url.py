from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import ChartData


urlpatterns = [
 #    url(r'^$', views.post_list, name='post_list'),
 #    url(r'^post/new/$', views.post_new, name='post_new'),
 #    url(r'^post/(?P<slug>[\w-]+)/$', views.post_detail, name='post_detail'),
 #    url(r'^post/(?P<slug>[\w-]+)/edit/$', views.post_edit, name='post_edit'),
 #    url(r'^post/(?P<slug>[\w-]+)/delete/$', views.post_delete, name='post_delete'),
	# url(r'^login/$', auth_views.login, {'template_name': 'registration/login.html'}, name='login'),
	# url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
	# url(r'^about/$', views.about, name='about'),
	url(r'^statistics/$', views.statistics, name='statistics'),
	url(r'^api/chart/data/$', ChartData.as_view()),
	url(r'^add_results/$', views.add_results, name='add_results'),

]

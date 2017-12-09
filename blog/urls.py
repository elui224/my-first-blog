from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from . import views
from .views import  (
		AboutView, 
		ChartData, 
		ChartSeasonData,
		ChartHeadtoHeadData,
		ChartPlayerData,
		ChartTotPlayerData,
		PostDetailView, 
		PostListView, 
		StatisticsView, 
		StatisticsHeadView,
		StatisticsSeasonView,
		StatisticsPlayerView,
		PostCreateView, 
		PostDeleteView, 
		PostUpdateView,
		SeasonPointView,
		)


urlpatterns = [

    url(r'^$', PostListView.as_view(), name='post_list'),
    url(r'^post/new/$', PostCreateView.as_view(), name='post_new'),
    url(r'^post/(?P<slug>[\w-]+)/$', PostDetailView.as_view(), name='post_detail'),
    url(r'^post/(?P<slug>[\w-]+)/edit/$', PostUpdateView.as_view(), name='post_edit'),
    url(r'^post/(?P<slug>[\w-]+)/delete/$', PostDeleteView.as_view(), name='post_delete'),
	url(r'^login/$', auth_views.login, {'template_name': 'registration/login.html'}, name='login'),
	url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
	url(r'^register/$', views.signup, name='register'),
	url(r'^about/$', AboutView.as_view(), name='about'),
	url(r'^statistics/$', StatisticsView.as_view(), name='statistics'),
	url(r'^statistics/season/$', StatisticsSeasonView.as_view(), name='statistics_season'),
	url(r'^statistics/h2h/$', StatisticsHeadView.as_view(), name='statistics_h2h'),
	url(r'^statistics/player/$', StatisticsPlayerView.as_view(), name='statistics_player'),
	url(r'^api/chart/data/$', ChartData.as_view()),
	url(r'^api/chart/seasondata/$', ChartSeasonData.as_view()),
	url(r'^api/chart/managerdata/$', ChartHeadtoHeadData.as_view()),
	url(r'^api/chart/playerdata/$', ChartPlayerData.as_view()),
	url(r'^api/chart/playertotaldata/$', ChartTotPlayerData.as_view()),
	url(r'^add_results/$', views.add_results, name='add_results'),
	url(r'^result/(?P<pk>[0-9]+)/$', views.edit_results, name='edit_results'),
	url(r'^delete_result/(?P<pk>[0-9]+)/$', views.delete_results, name='delete_results'),
	url(r'^add/$', SeasonPointView.as_view(), name='season_point'),
]


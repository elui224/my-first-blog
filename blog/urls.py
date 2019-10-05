from django.urls import re_path
from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView

from . import views
from .views import  (
		HomeView,
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
    re_path(r'^$', HomeView.as_view(), name='home'),   
    re_path(r'^post/$', PostListView.as_view(), name='post_list'),
    re_path(r'^post/new/$', PostCreateView.as_view(), name='post_new'),
    re_path(r'^post/(?P<slug>[\w-]+)/$', PostDetailView.as_view(), name='post_detail'),
    re_path(r'^post/(?P<slug>[\w-]+)/edit/$', PostUpdateView.as_view(), name='post_edit'),
    re_path(r'^post/(?P<slug>[\w-]+)/delete/$', PostDeleteView.as_view(), name='post_delete'),
	re_path(r'^login/$', LoginView.as_view(template_name='registration/login.html'), name='login'),
	re_path(r'^logout/$', LoginView.as_view(), name='logout'),
	re_path(r'^register/$', views.signup, name='register'),
	re_path(r'^about/$', AboutView.as_view(), name='about'),
	re_path(r'^statistics/$', StatisticsView.as_view(), name='statistics'),
	re_path(r'^statistics/season/$', StatisticsSeasonView.as_view(), name='statistics_season'),
	re_path(r'^statistics/h2h/$', StatisticsHeadView.as_view(), name='statistics_h2h'),
	re_path(r'^statistics/player/$', StatisticsPlayerView.as_view(), name='statistics_player'),
	re_path(r'^api/chart/data/$', ChartData.as_view()),
	re_path(r'^api/chart/seasondata/$', ChartSeasonData.as_view()),
	re_path(r'^api/chart/managerdata/$', ChartHeadtoHeadData.as_view()),
	re_path(r'^api/chart/playerdata/$', ChartPlayerData.as_view()),
	re_path(r'^api/chart/playertotaldata/$', ChartTotPlayerData.as_view()),
	re_path(r'^add_results/$', views.add_results, name='add_results'),
	re_path(r'^result/(?P<pk>[0-9]+)/$', views.edit_results, name='edit_results'),
	re_path(r'^delete_result/(?P<pk>[0-9]+)/$', views.delete_results, name='delete_results'),
	re_path(r'^add/$', SeasonPointView.as_view(), name='season_point'),
]


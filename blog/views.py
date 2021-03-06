from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, CreateView, ListView, DeleteView, UpdateView, FormView
from .forms import PostForm, GameForm, GoalForm, AssistForm, BaseGoalFormSet, BaseAssistFormSet, SeasonPointForm
from .models import Post, Game, Team, Goal, Player, Assist, SeasonPoint, Season, Year



from rest_framework.views import APIView
from rest_framework.response import Response


#This is a registration page to sign up
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
#This class view renders the statistics page.
class HomeView(TemplateView):
    template_name = "blog/home.html"

#This view returns all the posts in descending order.
class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts' 
    paginate_by = 5

    def get_queryset(self):
        today = timezone.now()
        if self.request.user.is_staff or self.request.user.is_superuser:
            queryset = Post.objects.all().filter(publish_date__lte=timezone.now()).order_by('-created_date')
        else:
            queryset = Post.objects.active()

        query = self.request.GET.get("search_query") #implements search function on main page.
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)|
                Q(bodytext__icontains=query)
                ).distinct()
        return queryset



# #This view returns an individual posts' details. Retrieve.
class PostDetailView(DetailView):
    model = Post


#class based view that allows one to create new blog posts.
class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = PostForm
    template_name = 'blog/post_edit.html'
    login_url = 'login'
    redirect_field_name = 'redirect_to'

    def test_func(self):
        return self.request.user.is_staff

    def get_login_url(self):
        if not self.request.user.is_authenticated:
            return super(UserSettingsView, self).get_login_url()
        else:
            return '/'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.author = self.request.user     
        return super(PostCreateView, self).form_valid(form) 

    def get_success_url(self):
        return reverse('post_detail', kwargs={"slug": self.object.slug})  


#This class renders the post edit views. NEEDS WORK.
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_edit.html' 
    login_url = 'login'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.author = self.request.user 
        return super(PostUpdateView, self).form_valid(form)  

    def get_success_url(self):
        return reverse('post_detail', kwargs={"slug": self.object.slug})  


#This class deletes posts.
class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')


#This view returns the About page view.
class AboutView(DetailView):
    template_name = 'blog/post_detail.html'

    def get_object(self):
        return get_object_or_404(Post,pk=1)


#This function returns the Add Results page view.
def add_results(request):
    num_games_display = 15
    game_list = Game.objects.all().order_by('-fifa_year', '-timestamp')
    page = request.GET.get('page', 1)
    paginator = Paginator(game_list, num_games_display)
    try:
        game = paginator.page(page)
    except PageNotAnInteger:
        game = paginator.page(1)
    except EmptyPage:
        game = paginator.page(paginator.num_pages)

    #So we do not have NoneType attribute errors when there are fewer than 2 season objects for the most recent year.
    #Creates two new season objects for the new year to the form of the web app started.
    if not Season.objects.filter(fifa_year__fifa_year__exact = Year.objects.values_list('fifa_year', flat=True).last()).exists():
        Season.objects.create(season_number=1, fifa_year=Year.objects.latest('id'), special_season_ind=0)
        Season.objects.create(season_number=2, fifa_year=Year.objects.latest('id'), special_season_ind=0)

    GoalFormSet = inlineformset_factory(Game, Goal, form= GoalForm, formset=BaseGoalFormSet, max_num= 10, extra= 1, can_delete = True) 
    AssistFormSet = inlineformset_factory(Game, Assist, form= AssistForm, formset=BaseAssistFormSet, max_num= 10, extra= 1, can_delete = True) 
    formset = GoalFormSet()
    formset_assists = AssistFormSet()

    if request.method == "POST":
        form = GameForm(request.POST or None)

        if form.is_valid():
            result = form.save(commit=False)
            result.author_game = request.user           
            formset = GoalFormSet(request.POST or None, instance=result)
            formset_assists = AssistFormSet(request.POST or None, instance=result)

            if all([gs.is_valid() for gs in formset]): #ensures all objects of formset is valid, if there are multiple objects.
                if all([gs_assist.is_valid() for gs_assist in formset_assists]):

                    result.save()
                    formset.save()
                    formset_assists.save()
                    messages.success(request, 'Results Added!')
                    return redirect('add_results')
            else:
                messages.warning(request, 'Submit Failed. Fix Errors.')
    else:
        form = GameForm()
        
    context = {
        'num_games_display': num_games_display,
        'form': form,
        'game': game,
        'paginator': paginator,
        'formset': formset,
        'formset_assists': formset_assists,
    }

    return render(request, 'blog/add_results.html', context)


#This functions allows result views to be editable. Update.
def edit_results(request, pk):
    game = get_object_or_404(Game, pk=pk)
    #So we do not have NoneType attribute errors when there are fewer than 2 season objects for the most recent year.
    #Creates two new season objects for the new year to the form of the web app started.
    if not Season.objects.filter(fifa_year__fifa_year__exact = Year.objects.values_list('fifa_year', flat=True).last()).exists():
        Season.objects.create(season_number=1, fifa_year=Year.objects.latest('id'), special_season_ind=0)
        Season.objects.create(season_number=2, fifa_year=Year.objects.latest('id'), special_season_ind=0)

    GoalFormSet = inlineformset_factory(Game, Goal, form= GoalForm, formset=BaseGoalFormSet, max_num= 10, extra= 1, can_delete = True) 
    AssistFormSet = inlineformset_factory(Game, Assist, form= AssistForm, formset=BaseAssistFormSet, max_num= 10, extra= 1, can_delete = True) 
    formset = GoalFormSet(instance=game)
    formset_assists = AssistFormSet(instance=game)

    if request.method == "POST":
        form = GameForm(request.POST or None, request.FILES, instance=game)
    

        if form.is_valid():
            result = form.save(commit=False)
            result.author_game = request.user 
            formset = GoalFormSet(request.POST or None, request.FILES, instance=game)
            formset_assists = AssistFormSet(request.POST or None, instance=game)

            if all([gs.is_valid() for gs in formset]): #ensures all objects of formset is valid, if there are multiple objects.
                if all([gs_assist.is_valid() for gs_assist in formset_assists]):
                    result.save()
                    formset.save()
                    formset_assists.save()
                    messages.success(request, 'Results Updated!')
                    return redirect('/add_results/')
            else:
                messages.warning(request, 'Update Failed. Fix Errors.')

    else:
        form = GameForm(instance=game)
        

    context = {
        'form': form,
        'formset': formset,
        'formset_assists': formset_assists,
    }

    return render(request, 'blog/edit_results.html', context)

#This view allows games (results) to be deleted.
def delete_results(request, pk=None):
    game = get_object_or_404(Game, pk=pk)
    game.delete()
    messages.success(request, 'Result Deleted!')
    return redirect('add_results')

#This class view renders the statistics page.
class StatisticsView(TemplateView):
    template_name = "blog/statistics.html"

#This class view renders the statistics page.
class StatisticsSeasonView(TemplateView):
    template_name = "blog/statistics_season.html"

#This class view renders the statistics page.
class StatisticsHeadView(TemplateView):
    template_name = "blog/statistics_h2h.html"


#This class view renders the statistics page.
class StatisticsPlayerView(TemplateView):
    template_name = "blog/statistics_player.html"



#Class view displays data view. Function returns data for charts in blog/statistics.html.
class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        resultset = Game.get_game_data()
        data = resultset
        return Response(data)

#Class view displays data view. Function returns data for charts in blog/statistics/season.html.
class ChartSeasonData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        seasonset = Game.get_season_game_data()
        data = seasonset
        return Response(data)

#Class view displays data view. Function returns data for charts in blog/statistics/headtoheaddata.html.
class ChartHeadtoHeadData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        h2hset = Game.get_headtohead_data()
        data = h2hset
        return Response(data)

#Class view displays data view. Function returns data for charts in blog/statistics/player.html.
class ChartPlayerData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        playerset = Goal.get_goal_against_data()
        data = playerset
        return Response(data)

class ChartTotPlayerData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        playerdataset = Player.get_tot_player_data()
        data = playerdataset
        return Response(data)   

from . import services
class SeasonPointView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'blog/season_point.html'
    form_class = SeasonPointForm
    login_url = 'login'
    redirect_field_name = 'redirect_to'
    success_url = '/add/'
    success_message = "Added successfully!"

    def form_valid(self, form):
        form.save()   
        return super(SeasonPointView, self).form_valid(form) 

    def get(self,request):
        price_list = services.get_price()
        # query = self.request.GET.get("search_query") #implements search function on main page.
        # if query:
        #     price_list = price_list.filter(
        #         Q(title__icontains=query)|
        #         Q(bodytext__icontains=query)
        #         ).distinct()
        print ([ d["name"] for d in price_list ])
        return render(request,'blog/season_point.html', {'price_list': price_list})


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, TemplateView, CreateView, ListView, DeleteView, UpdateView
from .forms import PostForm, GameForm, GoalForm, BaseGoalFormSet
from .models import Post, Game, Team, Goal, Player


from rest_framework.views import APIView
from rest_framework.response import Response


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
class PostCreateView(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'blog/post_edit.html'
    login_url = 'login'
    redirect_field_name = 'redirect_to'

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
    # if request.user.is_authenticated():
    num_games_display = 15
    game = Game.objects.all().order_by('-timestamp')[:num_games_display]
    GoalFormSet = inlineformset_factory(Game, Goal, form= GoalForm, formset=BaseGoalFormSet, max_num= 10, extra= 1, can_delete = True) 
    formset = GoalFormSet()

    if request.method == "POST":
        form = GameForm(request.POST or None)

        if form.is_valid():
            result = form.save(commit=False)
            formset = GoalFormSet(request.POST or None, instance=result)

            if formset.is_valid():
                result.save()
                formset.save()
                messages.success(request, 'Results Added!')
                return redirect('add_results')


    else:
        form = GameForm()
        
    context = {
        'num_games_display': num_games_display,
        'form': form,
        'game': game,
        'formset': formset
    }

    return render(request, 'blog/add_results.html', context)

    # else:
    #     return redirect('login')

#This functions allows result views to be editable. Update.
def edit_results(request, pk):
    # if request.user.is_authenticated():
    game = get_object_or_404(Game, pk=pk)
    GoalFormSet = inlineformset_factory(Game, Goal, form= GoalForm, formset=BaseGoalFormSet, max_num= 10, extra= 1, can_delete = True) 
    formset = GoalFormSet(instance=game)

    if request.method == "POST":
        form = GameForm(request.POST or None, request.FILES, instance=game)
    

        if form.is_valid():
            result = form.save(commit=False)
            formset = GoalFormSet(request.POST or None, request.FILES, instance=game)

            if formset.is_valid():
                result.save()
                formset.save()
                messages.success(request, 'Result Updated!')
                return redirect('/add_results/')

    else:
        form = GameForm(instance=game)
        

    context = {
        'form': form,
        'formset': formset,
    }

    return render(request, 'blog/edit_results.html', context)

    # else:
    #     return redirect('login')



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




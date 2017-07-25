from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, TemplateView, CreateView, ListView
from django.views.generic import View
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

#This function opens a form to easily edit blog posts. Create.
@login_required()
def post_new(request):
    # if request.user.is_staff or request.user.is_superuser:
        if request.method == "POST":
            form = PostForm(request.POST, request.FILES or None)

            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                # post.publish_date = timezone.now()
                post.save()
                return redirect('post_detail', slug=post.slug)

        else:
            form = PostForm()

        return render(request, 'blog/post_edit.html', {'form': form})

    # else:
    #     return redirect('login')

# #class based view that allows one to create new blog posts.
# class PostCreateView(CreateView):
#     form_class = PostForm
#     template_name = 'blog/post_edit.html'

#     def form_valid(self, form):
#         instance = form.save(commit=False)
#         instance.author = self.request.user
#         return super(PostCreateView, self).form_valid(form)



#This functions allows blog views to be editable. Update.
@login_required()
def post_edit(request, slug):
    #if request.user.is_staff or request.user.is_superuser:
        post = get_object_or_404(Post, slug=slug)

        if request.method == "POST":
            form = PostForm(request.POST, request.FILES or None, instance=post)

            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                # post.publish_date = timezone.now()
                post.save()
                return redirect('post_detail', slug=post.slug)

        else:
            form = PostForm(instance=post)

        return render(request, 'blog/post_edit.html', {'form': form})

    #else:
        #return redirect('login')

#This functions allows blog posts to be deleted. Delete.
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.delete()
    return redirect('post_detail')

#This view returns the About page view.
class AboutView(TemplateView):
    template_name = 'blog/post_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(AboutView, self).get_context_data(*args, **kwargs)
        post = get_object_or_404(Post, pk=1)
        context = {
            'post': post
        }
        return context

#This function returns the Add Results page view.
def add_results(request):
    if request.user.is_authenticated():
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

    else:
        return redirect('login')

#This functions allows result views to be editable. Update.
def edit_results(request, pk):
    if request.user.is_authenticated():
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

    else:
        return redirect('login')


# #This function returns the Statistics page view.
# def statistics(request):
#     data = Game.get_game_data()
#     return render(request, 'blog/statistics.html', {'data':data})

#This class view renders the statistics page.
class StatisticsView(TemplateView):
    template_name = "blog/statistics.html"

    def get_goals(self):
        goal_data = Goal.get_goal_data()
        return goal_data


#Class view displays data view. Function returns data for charts in blog/statistics.html.
class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        resultset = Game.get_game_data()
        data = resultset
        return Response(data)



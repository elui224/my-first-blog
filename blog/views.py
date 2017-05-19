from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import View
from .forms import PostForm, GameForm, GoalForm, BaseGoalFormSet
from .models import Post, Game, Team, Goal, Player

from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.

#This function returns all the posts in descending order.
def post_list(request):
    today = timezone.now()
    if request.user.is_staff or request.user.is_superuser:
        posts = Post.objects.all().filter(publish_date__lte=timezone.now()).order_by('-created_date')
    else:
        posts = Post.objects.active()
    query = request.GET.get("search_query") #implements search function on main page.

    if query:
        posts = posts.filter(
            Q(title__icontains=query)|
            Q(bodytext__icontains=query)
            ).distinct()

    paginator = Paginator(posts, 5)
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, 'blog/post_list.html', {'posts': posts})

#This function returns an individual post in its own view to display more details. Retrieve.
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.publish_date > timezone.now() or post.draft:
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404

    return render(request, 'blog/post_detail.html', {'post': post})

#This function opens a form to easily edit blog posts. Create.
def post_new(request):
    if request.user.is_authenticated():
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

    else:
        return redirect('login')

#This functions allows blog views to be editable. Update.
def post_edit(request, slug):
    if request.user.is_authenticated():
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

    else:
        return redirect('login')

#This functions allows blog posts to be deleted. Delete.
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.delete()
    return redirect('post_detail')

#This function returns the About page view.
def about(request):
    post = get_object_or_404(Post, pk=1)
    return render(request, 'blog/post_detail.html', {'post': post})

#This function returns the Add Results page view.
def add_results(request):
    if request.user.is_authenticated():

        game = Game.objects.all().order_by('-timestamp')[:10]
        GoalFormSet = inlineformset_factory(Game, Goal, form= GoalForm, formset=BaseGoalFormSet, max_num= 10, extra= 1) 
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
            'form':form,
            'game':game,
            'formset': formset
        }

        return render(request, 'blog/add_results.html', context)

    else:
        return redirect('login')


#This function returns the Statistics page view.
def statistics(request):
    data = Game.get_player_data()
    return render(request, 'blog/statistics.html', {'data':data})

#Class view displays data view. Function get returns data for charts in blog/statistics.html.
class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        resultset = Game.get_player_data()
        data = resultset
        return Response(data)



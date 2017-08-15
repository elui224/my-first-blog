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

# Create your views here.

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



#This class view renders the statistics page.
class StatisticsView(TemplateView):
    template_name = "blog/statistics.html"

    def goals(self):
        queryset = Goal.objects.goals_against()

        # query = self.request.GET.get("search_filter_query") #implements search function on main page.
        # if query:
        #     queryset = queryset.filter(
        #         Q(player__icontains=query)|
        #         Q(opponent_scored_on__icontains=query)
        #         ).distinct()
        return queryset


#Class view displays data view. Function returns data for charts in blog/statistics.html.
class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        resultset = Game.get_game_data()
        data = resultset
        return Response(data)



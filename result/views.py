from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import View
from .forms import GameForm, GoalForm, BaseGoalFormSet
from .models import Game, Team, Goal, Player

from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.

#This function returns all the posts in descending order.

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



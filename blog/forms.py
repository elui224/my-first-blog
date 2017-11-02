from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils.safestring import mark_safe
from .models import Post, Game, Player, Goal, Season, Assist

from crispy_forms.helper import FormHelper


class PostForm(forms.ModelForm):

	class Meta:
		model = Post
		fields = ['title', 'bodytext','image', 'draft', 'publish_date',]


class GameForm(forms.ModelForm):

	class Meta:
		model = Game
		fields = ["your_first_name","opponent_first_name","your_score","opponent_score"]
		labels = {
			'your_first_name': 'Your Name',
			'opponent_first_name': 'Your Opponent',
			'your_score': 'Your Score',
			'opponent_score': 'Opponent Score',
		}
		widgets = {
			#This widget allows the foreign key field to display as a radio question.
			"your_first_name": forms.RadioSelect(),
			"opponent_first_name": forms.RadioSelect(),
		}

	def __init__(self, *args, **kwargs): #This function removes the empty label option in radio select.
		super(GameForm, self).__init__(*args, **kwargs)
		self.fields['your_first_name'].empty_label = None
		self.fields['opponent_first_name'].empty_label = None


	def clean(self, *args, **kwargs): 
		#For radioselect, must check if fields exist before requirement validation kicks in. Will cause error if this is not here.
		if self.cleaned_data.get('your_first_name') and self.cleaned_data.get('opponent_first_name'): 
			try:
				cleaned_data = super(GameForm, self).clean()
				your_first_name = self.cleaned_data['your_first_name']
				opponent_first_name = self.cleaned_data['opponent_first_name']
				if your_first_name == opponent_first_name:
					raise forms.ValidationError('You cannot play against yourself!')
				return cleaned_data
			except AttributeError: #The try-except pattern guards against an AttributeError sometimes arising when cleaning data
				pass

	

class GoalForm(forms.ModelForm):

	class Meta:
		model = Goal
		fields = ["player_name","num_goals"]
		labels = {
			'player_name': 'Goal Scorer',
			'num_goals': 'Total Goals',
		}


class AssistForm(forms.ModelForm):

	class Meta:
		model = Assist
		fields = ["player_name","num_assists"]
		labels = {
			'player_name': 'Assist Getter',
			'num_assists': 'Total Assists',
		}


class BaseGoalFormSet(BaseInlineFormSet):

	def clean(self, *args, **kwargs):
		try:
			super(BaseGoalFormSet, self).clean()
			if any(self.errors):
				return

			player_names = []
			num_goals = [] # need to validate sum of goal scorers is equal to goals of home + away teams. 
			#Parent's form instance gets preserved before clean method gets called, so should be available

			for form in self.forms:
				if form.cleaned_data:
					player_name = form.cleaned_data['player_name']

					if player_name:
						if player_name in player_names:
							raise forms.ValidationError('Goal scorers must be unique.')
						player_names.append(player_name)

		except AttributeError:
			pass

class BaseAssistFormSet(BaseInlineFormSet):

	def clean(self, *args, **kwargs):
		try:
			super(BaseAssistFormSet, self).clean()
			if any(self.errors):
				return

			player_names = []
			num_assist = [] # need to validate sum of goal scorers is equal to goals of home + away teams. 
			#Parent's form instance gets preserved before clean method gets called, so should be available

			for form in self.forms:
				if form.cleaned_data:
					player_name = form.cleaned_data['player_name']

					if player_name:
						if player_name in player_names:
							raise forms.ValidationError('Assist getters must be unique.')
						player_names.append(player_name)

		except AttributeError:
			pass



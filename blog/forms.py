from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Post, Game, Player, Goal, Season


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


	def clean(self, *args, **kwargs):
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



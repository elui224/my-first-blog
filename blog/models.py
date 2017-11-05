
from datetime import datetime
# from datetime import date
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max, Sum, Count
from django.db.models import signals
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify
import json
from django.core.serializers.json import DjangoJSONEncoder
from markdown_deux import markdown
from PIL import Image

class PostQuerySet(models.query.QuerySet): #custom queryset to handle queries to return posts.
	def not_draft(self):
		return self.filter(draft=False)

	def published(self):
		return self.filter(publish_date__lte=timezone.now()).not_draft()


class PostManager(models.Manager):
	def get_queryset(self, *args, **kwargs):
		return PostQuerySet(self.model, using=self._db)

	def active(self, *args, **kwargs):
		# return super(PostManager, self).filter(draft=False).filter(publish_date__lte=timezone.now()).order_by('-created_date')
		return self.get_queryset().published().order_by('-created_date')


def img_upload_location(instance, filename):
	return "%s/%s" %(instance.slug, filename)

class Post(models.Model):
	author 			= models.ForeignKey('auth.User')
	title 			= models.CharField(max_length = 100)
	draft 			= models.BooleanField(default = False)
	slug 			= models.SlugField(unique = True)
	image 			= models.ImageField(upload_to=img_upload_location,
						null = True,
						blank = True, 
						height_field = "height_field", 
						width_field = "width_field")
	height_field 	= models.IntegerField(default=0, null=True, blank = True)
	width_field 	= models.IntegerField(default=0, null=True, blank = True)
	bodytext 		= models.TextField()
	created_date 	= models.DateTimeField(default = timezone.now)
	publish_date 	= models.DateTimeField(default = timezone.now, auto_now = False, auto_now_add = False)
	objects 		= PostManager()

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		return reverse("posts:detail", kwargs={"slug": self.slug})

	def publish(self):
		self.published_date = timezone.now()
		self.save()

	def get_html(self):
		bodytext = self.bodytext
		markdown_bodytext = markdown(bodytext)
		return mark_safe(markdown_bodytext)


'''
Create random slug number instead of pk.
'''
from blog.utils import unique_slug_generator

def pre_save_post_receiver(sender, instance, *args, **kwargs): #creates a new slug for a post before saving.
	if not instance.slug:
		# instance.slug = create_slug(instance)
		instance.slug = unique_slug_generator(instance)

pre_save.connect(pre_save_post_receiver, sender=Post)


class Team(models.Model):
	manager_name 	= models.CharField(max_length = 50, default = None)
	ACTIVE 			= 'A'
	INACTIVE 		= 'I'
	STATUS_CHOICES 	= (
					(ACTIVE, 'Active'),
					(INACTIVE, 'Inactive')
					)
	rec_status 		= models.CharField(max_length = 1, default = ACTIVE, choices = STATUS_CHOICES)
	team_image 		= models.ImageField(
					upload_to 		= img_upload_location,
					null 			= True,
					blank 			= True, 
					height_field 	= "height_field", 
					width_field 	= "width_field"
					)
	height_field 	= models.IntegerField(default=0, null=True, blank = True)
	width_field 	= models.IntegerField(default=0, null=True, blank = True)
	profile_text 	= models.TextField(null = True, blank = True)

	def __str__(self):
		return self.manager_name

	def get_active_teams():
		active_teams = Team.objects.filter(rec_status='A').values_list('manager_name', flat = True)
		return active_teams

	def get_active_teams_count():
		active_teams_count = Team.objects.filter(rec_status='A').count()
		return active_teams_count



class Player(models.Model):
	team 					= models.ForeignKey(Team, on_delete = models.CASCADE) #Each player can belong to multiple teams as they get traded.
	player_name 			= models.CharField(max_length = 100)
	player_position 		= models.CharField(max_length = 4, null = True, blank = True)
	ACTIVE 					= 'A'
	INACTIVE 				= 'I'
	STATUS_CHOICES 			= (
								(ACTIVE, 'Active'),
								(INACTIVE, 'Inactive')
							)
	player_team_rec_status 	= models.CharField(max_length = 1, default = ACTIVE, choices = STATUS_CHOICES)


	def __str__(self):
		return str(self.player_name)

	class Meta:
		ordering = ('player_name',)

	def get_tot_player_data():

		query_player_tot = '''
		SELECT id, player_name, tot_goal, tot_assist 
		FROM (
			SELECT id, player_name 
			FROM blog_player
			) player
		LEFT JOIN
		(
			SELECT player_name_id, sum(num_goals) tot_goal 
			FROM blog_goal
			group by player_name_id
		) goal
		ON player.id = goal.player_name_id
		LEFT JOIN
		(
			SELECT player_name_id, sum(num_assists) tot_assist 
			FROM blog_assist
			group by player_name_id
		) assist
		ON player.id = assist.player_name_id
		order by tot_goal desc
		'''
	
		tot_player_data_query = Player.objects.raw(query_player_tot)

		tot_player_data = []

		for row in tot_player_data_query:
			r = ({"id": row.id, "player": row.player_name, "goals": row.tot_goal, "assists": row.tot_assist})
			tot_player_data.append(r)

		return tot_player_data



class Year(models.Model):
	fifa_year = models.PositiveIntegerField(default=1)

	def __str__(self):
		return '{} {}'.format('Fifa Year', self.fifa_year)

def get_current_year_number():
	year_qs = Year.objects.all()
	year_exists = year_qs.exists()
	if year_exists:
		current_year_object = Year.objects.latest('fifa_year')
		set_action_date = "2017-07-12 16:55:00" #yyyy/mm/dd h:m:s  #release date of fifa18.
		date_format = "%Y-%m-%d %H:%M:%S"
		now = datetime.now().strftime(date_format)
		# fifa_release_date = datetime.strptime(set_action_date, date_format) 
		current_fifa_year = Year.objects.all().aggregate(Max('fifa_year'))['fifa_year__max']
		if datetime.now().strftime(date_format) == set_action_date:
			next_fifa_year = current_fifa_year + 1
			Year.objects.create(fifa_year=next_fifa_year)
			default_year_object = current_year_object
	else:
		default_year_object = Year.objects.create(fifa_year=1)
	return default_year_object



class Season(models.Model):
	fifa_year 		= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE) 
	season_number 	= models.PositiveIntegerField()

	def __str__(self):
		return '{} {}'.format('Season', self.season_number)



def get_default_season_number(): 
#Returns the current season based on number of games played to display.
	active_teams_count = Team.get_active_teams_count()
	season_games_against_opponent = 2
	opponents_per_season = active_teams_count - 1
	total_games_per_season = active_teams_count * season_games_against_opponent * opponents_per_season / 2

	season_qs = Season.objects.all()
	season_exists = season_qs.exists()

	if season_exists:
		prev_season_object = Season.objects.all().order_by('-season_number')[1]
		current_season_object = Season.objects.latest('season_number')

		current_season_number = Season.objects.all().aggregate(Max('season_number'))['season_number__max']
		prev_season_game_count = Game.objects.filter(season_number__season_number = current_season_number - 1).count()
		current_season_game_count = Game.objects.filter(season_number__season_number = current_season_number ).count()
		
		if prev_season_game_count < total_games_per_season:
			default_season_number = prev_season_object

		elif current_season_game_count < total_games_per_season:
			default_season_number = current_season_object

		else:
			#create new instance of Season. Increment default_season_number by 1.
			current_fifa_year_id = Year.objects.latest('id') 
			next_season = current_season_number + 1
			Season.objects.create(season_number=next_season, fifa_year=current_fifa_year_id)
			default_season_number = current_season_object
			
	else:
		default_season_number = None

	return default_season_number


class Game(models.Model):
	season_number 			= models.ForeignKey(Season, null = True,  default = get_default_season_number, on_delete = models.CASCADE) 
	your_first_name 		= models.ForeignKey(Team, on_delete = models.CASCADE, related_name = 'your_first_name')
	opponent_first_name 	= models.ForeignKey(Team, on_delete = models.CASCADE, related_name = 'opponent_first_name')
	your_score 				= models.PositiveIntegerField()
	opponent_score 			= models.PositiveIntegerField()
	your_result 			= models.PositiveIntegerField(editable=False)
	opponent_result 		= models.PositiveIntegerField(editable=False)
	timestamp 				= models.DateTimeField(auto_now_add=True, auto_now=False)
	updated 				= models.DateTimeField(auto_now_add=False, auto_now=True)	

	def __str__(self):
		return '{} vs {}'.format(self.your_first_name.manager_name, self.opponent_first_name.manager_name) 

	#Converts your_result and opponent_result attribute based on form inputs by 
	#overriding save method of form.
	def save(self, *args, **kwargs):

		if self.your_score > self.opponent_score:
			self.your_result = 3
			self.opponent_result = 0
		elif self.your_score < self.opponent_score:
			self.your_result = 0
			self.opponent_result = 3
		else:
			self.your_result = 1
			self.opponent_result = 1
		super(Game, self).save(*args, **kwargs)

	#add method to return game data to populate data display.
	def get_game_data():

		data = {
		'number_games': [],
		'total_points':[],
		'goals':[],
		'goal_diff':[],
		'number_wins':[],
		'number_ties':[],
		'number_losses':[],
		'manager_name':[]
		}

		query = '''
		SELECT id, 
			manager_name
			, rec_status
			, sum(total_points) AS total_points
			, sum(goals) AS goals
			, sum(goal_diff) AS goal_diff
			, count(total_points) AS number_games 
			, sum(case when total_points = 3 then 1 end) AS number_wins
			, sum(case when total_points = 1 then 1 end) AS number_ties
			, sum(case when total_points = 0 then 1 end) AS number_losses
		FROM (
			SELECT 
				blog_team.id
				, blog_team.manager_name
				, blog_team.rec_status
				, blog_game.your_result AS total_points 
				, blog_game.your_score AS goals
				, cast(blog_game.your_score as signed) - cast(blog_game.opponent_score as signed) AS goal_diff
			FROM blog_team LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.your_first_name_id) 

			UNION ALL 

			SELECT 
				blog_team.id
				, blog_team.manager_name
				, blog_team.rec_status
				, blog_game.opponent_result AS total_points 
				, blog_game.opponent_score AS goals
				, cast(blog_game.opponent_score as signed) - cast(blog_game.your_score as signed) AS goal_diff
			FROM blog_team LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.opponent_first_name_id)
		) AGGREGATED 
		WHERE rec_status = 'A'
		GROUP BY id, manager_name, rec_status
		'''

		teams = Team.objects.raw(query)


		for info in teams:
			data['manager_name'].append(info.manager_name)
			data['total_points'].append(int(info.total_points or 0)) #adding or 0 prevents NoneType error.
			data['goals'].append(int(info.goals or 0))
			data['goal_diff'].append(int(info.goal_diff or 0))
			data['number_games'].append(info.number_games)
			data['number_wins'].append(info.number_wins)
			data['number_ties'].append(info.number_ties)
			data['number_losses'].append(info.number_losses)

		return data

	def get_season_game_data():

		query_season = '''
		SELECT 
			id
			, manager_name
			, season_number
			, sum(case when total_points = 3 then 1 else 0 end) AS number_wins
			, sum(case when total_points = 1 then 1 else 0 end) AS number_ties
			, sum(case when total_points = 0 then 1 else 0 end) AS number_losses
			, sum(total_points) AS total_points
			, sum(goals) AS goals
			, sum(goal_diff) AS goal_diff
			, count(total_points) AS number_games 

		FROM (
				
			SELECT 
				blog_team.id
				, blog_season.season_number
				, blog_team.manager_name
				, blog_team.rec_status
				, blog_game.your_result AS total_points 
				, blog_game.your_score AS goals
				, cast(blog_game.your_score as signed) - cast(blog_game.opponent_score as signed) AS goal_diff
			FROM blog_team 
			LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.your_first_name_id) 
			LEFT OUTER JOIN blog_season ON (blog_game.season_number_id = blog_season.id)
			WHERE blog_team.rec_status = 'A'
			
			UNION ALL 
			
			SELECT 
				blog_team.id
				, blog_season.season_number
				, blog_team.manager_name
				, blog_team.rec_status
				, blog_game.opponent_result AS total_points 
				, blog_game.opponent_score AS goals
				, cast(blog_game.opponent_score as signed) - cast(blog_game.your_score as signed) AS goal_diff
			FROM blog_team 
			LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.opponent_first_name_id) 
			LEFT OUTER JOIN blog_season ON (blog_game.season_number_id = blog_season.id)
			WHERE blog_team.rec_status = 'A'
			) AGGREGATED 
		WHERE season_number is not null
		GROUP BY id, manager_name, rec_status, season_number
		ORDER BY SEASON_NUMBER
		'''

		seasonal_data = Team.objects.raw(query_season)

		rows = []
		for row in seasonal_data:
			r = ({"season":"Season " + str(row.season_number), "manager": row.manager_name, "wins": row.number_wins, "ties": row.number_ties, "losses": row.number_losses
				, "points": row.total_points, "goals": row.goals, "GD": row.goal_diff, "games": row.number_games})
			rows.append(r)


		return rows

	def get_headtohead_data():

		query_headtohead = '''
		select 
		 stats.player as id
		, stats.opponent opponent
		, sum(number_wins) wins
		, sum(number_ties) ties
		, sum(number_losses) losses
		, sum(result) total_points
		, sum(goal_diff) GD
		, count(result) games
			from (
			select blog_game.id, t.manager_name as player, te.manager_name as opponent 
			, your_result result
			, case when blog_game.your_result = 3 then 1 else 0 end AS number_wins
			, case when blog_game.your_result = 1 then 1 else 0 end AS number_ties
			, case when blog_game.your_result = 0 then 1 else 0 end AS number_losses
			, cast(blog_game.your_score as signed) - cast(blog_game.opponent_score as signed) AS goal_diff

			from blog_game
			inner join blog_team t on blog_game.your_first_name_id = t.id
			inner join blog_team te on blog_game.opponent_first_name_id = te.id

			union all 

			select blog_game.id, t.manager_name as player, te.manager_name as opponent 
			, opponent_result result
			, case when blog_game.opponent_result = 3 then 1 else 0 end AS number_wins
			, case when blog_game.opponent_result = 1 then 1 else 0 end AS number_ties
			, case when blog_game.opponent_result = 0 then 1 else 0 end AS number_losses
			, cast(blog_game.opponent_score as signed) - cast(blog_game.your_score as signed) AS goal_diff

			from blog_game
			inner join blog_team t on blog_game.opponent_first_name_id = t.id
			inner join blog_team te on blog_game.your_first_name_id = te.id

			) stats
		group by stats.player, stats.opponent
		'''

		headtohead_data = Game.objects.raw(query_headtohead)

		rows = []
		for row in headtohead_data:
			r = ({"player": row.id, "opponent": row.opponent, "wins": row.wins, "ties": row.ties, "losses": row.losses
				, "points": row.total_points, "GD": row.GD, "games": row.games})
			rows.append(r)

		return rows

#Returns the current game
def get_default_game_number(): 
	game_qs = Game.objects.all()
	game_exists = game_qs.exists()

	if game_exists:
		current_game_object = Game.objects.latest('id')
		
	else:
		current_game_object = None

	return current_game_object


class Goal(models.Model):
	player_name = models.ForeignKey(Player, on_delete = models.CASCADE)
	game 		= models.ForeignKey(Game, default = get_default_game_number, on_delete = models.CASCADE)
	num_goals 	= models.PositiveIntegerField(null = True)

	def __str__(self):
		return '{} {}'.format("Game",self.game) 


	def get_goal_against_data():

		query_player = '''
		select goals.*, assists.tot_assists from (
			SELECT id, mgr, player, blog_team.manager_name opponent_scored_on, sum(num_goals) tot_goals FROM (
					SELECT blog_player.player_name player, blog_team.manager_name mgr, blog_goal.num_goals, case 
						when blog_player.team_id = blog_game.opponent_first_name_id then blog_game.your_first_name_id 
						when blog_player.team_id = blog_game.your_first_name_id then blog_game.opponent_first_name_id end opponent
					FROM blog_player
					INNER JOIN
					blog_team ON blog_player.team_id = blog_team.id
					INNER JOIN 
					blog_goal ON blog_player.id = blog_goal.player_name_id
					INNER JOIN
					blog_game ON blog_game.id = blog_goal.game_id
					where player_team_rec_status = 'A'
					) data1
				INNER JOIN 
				blog_team ON data1.opponent = blog_team.id
				WHERE opponent is not null
				GROUP BY id, mgr, player, opponent_scored_on
				ORDER BY player, mgr, tot_goals
				) goals
				
			left outer join
			
			(
			SELECT player, blog_team.manager_name opponent_scored_on,sum(num_assists) tot_assists FROM (
					SELECT blog_player.player_name player, blog_team.manager_name mgr, blog_assist.num_assists, case 
						when blog_player.team_id = blog_game.opponent_first_name_id then blog_game.your_first_name_id 
						when blog_player.team_id = blog_game.your_first_name_id then blog_game.opponent_first_name_id end opponent
					FROM blog_player
					INNER JOIN
					blog_team ON blog_player.team_id = blog_team.id
					INNER JOIN 
					blog_assist ON blog_player.id = blog_assist.player_name_id
					INNER JOIN
					blog_game ON blog_game.id = blog_assist.game_id
					where player_team_rec_status = 'A'
					) data1
				INNER JOIN 
				blog_team ON data1.opponent = blog_team.id
				WHERE opponent is not null
				GROUP BY player,opponent_scored_on
				ORDER BY player
				) assists
			on goals.player = assists.player
			and goals.opponent_scored_on = assists.opponent_scored_on
	'''
	
		goal_against_data = Player.objects.raw(query_player)

		goal_against_rows = []

		for row in goal_against_data:
			r = ({"id":row.id, "manager": row.mgr, "player": row.player, "mgr": row.opponent_scored_on, "goals": row.tot_goals, "assists": row.tot_assists})
			goal_against_rows.append(r)


		return goal_against_rows

class Assist(models.Model):
	player_name = models.ForeignKey(Player, on_delete = models.CASCADE)
	game 		= models.ForeignKey(Game, default = get_default_game_number, on_delete = models.CASCADE)
	num_assists 	= models.PositiveIntegerField(null = True)

	def __str__(self):
		return '{} {}'.format("Assist",self.game) 


	# def get_goal_against_data():

	# 	query_player = '''
	# 		SELECT id, mgr, player, blog_team.manager_name opponent_scored_on, sum(num_goals) tot_goals FROM (
	# 			SELECT blog_player.player_name player, blog_team.manager_name mgr, blog_goal.num_goals, case 
	# 				when blog_player.team_id = blog_game.opponent_first_name_id then blog_game.your_first_name_id 
	# 				when blog_player.team_id = blog_game.your_first_name_id then blog_game.opponent_first_name_id end opponent
	# 			FROM blog_player
	# 			INNER JOIN
	# 			blog_team ON blog_player.team_id = blog_team.id
	# 			INNER JOIN 
	# 			blog_goal ON blog_player.id = blog_goal.player_name_id
	# 			INNER JOIN
	# 			blog_game ON blog_game.id = blog_goal.game_id
	# 			where player_team_rec_status = 'A'
	# 			) data1
	# 		INNER JOIN 
	# 		blog_team ON data1.opponent = blog_team.id
	# 		WHERE opponent is not null
	# 		GROUP BY id, mgr, player, opponent_scored_on
	# 		ORDER BY player, mgr, tot_goals
	# 	'''

	# 	goal_against_data = Player.objects.raw(query_player)

	# 	goal_against_rows = []

	# 	for row in goal_against_data:
	# 		r = ({"id":row.id, "manager": row.mgr, "player": row.player, "mgr": row.opponent_scored_on, "goals": row.tot_goals})
	# 		goal_against_rows.append(r)


	# 	return goal_against_rows





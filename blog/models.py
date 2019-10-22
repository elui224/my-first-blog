
from datetime import datetime
# from datetime import date
from django.urls import reverse
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
	author 			= models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
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



class Year(models.Model):
	fifa_year = models.PositiveIntegerField(default=1)

	def __str__(self):
		return '{} {}'.format('Fifa Year', self.fifa_year)

def get_current_year_number():
	year_qs = Year.objects.all()
	year_exists = year_qs.exists()
	if year_exists:
		current_year_object = Year.objects.latest('id') 
		default_year_number = current_year_object.id
	return default_year_number



class Season(models.Model):
	fifa_year 			= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE) 
	season_number 		= models.PositiveIntegerField()
	special_season_ind	= models.IntegerField(default=0)

	def __str__(self):
		return '{} {}'.format('Season', self.season_number)



def get_default_season_number(): #Need to think of way to reset counter of seasons after new fifa year.
#Returns the current season based on number of games played to display.
	active_teams_count = Team.get_active_teams_count()
	# active_teams_count = 4
	season_games_against_opponent = 2
	opponents_per_season = active_teams_count - 1

	current_fifa_year_id = Year.objects.latest('id') #added year filter to grab the latest fifa year for counts
	
	try:
		prev_season_object = Season.objects.filter(fifa_year_id = current_fifa_year_id).all().order_by('-season_number')[1]
	except:
		prev_season_object = None
		
	current_season_object = Season.objects.filter(fifa_year_id = current_fifa_year_id).latest('season_number')

	current_season_number = Season.objects.filter(fifa_year_id = current_fifa_year_id).aggregate(Max('season_number'))['season_number__max']	
	prev_season_game_count = Game.objects.filter(fifa_year_id = current_fifa_year_id).filter(season_number__season_number = current_season_number - 1).count()
	current_season_game_count = Game.objects.filter(fifa_year_id = current_fifa_year_id).filter(season_number__season_number = current_season_number ).count()

	'''
	Determines the number of games in the season.
	The total_games_per_season is a variable used for logical comparison below.
	Special seasons have a different number of games than regular seasons.
	'''
	if (prev_season_object.special_season_ind == 0 and current_season_game_count == 0) or (current_season_object.special_season_ind == 0 and prev_season_object.special_season_ind == 1 and current_season_game_count > 0 and prev_season_game_count > 0):
		total_games_per_season = active_teams_count * season_games_against_opponent * opponents_per_season / 2
	else:
		gm_round_one = 4 * active_teams_count / 2 # four games per person. Divide by 2 for unique games in round 1.
		gm_consolation = 1 * 2 / 2 # 1 game per person. Divide by 2 for unique games.
		gm_semi = 1 * 4 / 2 #Divide by 2 for unique games.
		gm_finals = gm_consolation
		gm_second_place = gm_consolation
		num_games_special_season = gm_round_one + gm_consolation + gm_semi + gm_finals + gm_second_place
		total_games_per_season = num_games_special_season
		# total_games_per_season = 3

	season_exists = Season.objects.all().exists()

	if season_exists: #Determines the season number to prepopulate each game form. The season number field is hidden.			
		if prev_season_game_count < total_games_per_season and prev_season_object.special_season_ind == 0:
			default_season_number = prev_season_object

		elif current_season_game_count < total_games_per_season:
			default_season_number = current_season_object

		else:
			#create new instance of Season. Increment default_season_number by 1. 
			next_season = current_season_number + 1
			if next_season % 4 == 0: #This determines if the new object will be a special season or not. Special seasons happen every four years.
				special_season = 1
			else:
				special_season = 0
			Season.objects.create(season_number=next_season, fifa_year=current_fifa_year_id, special_season_ind = special_season)
			default_season_number = current_season_object
			
	else:
		default_season_number = None

	return default_season_number



class Player(models.Model):
	#Add fifa year to the player model 9.15.2018
	fifa_year 				= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE)
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
		SELECT player.id, fifa_year, player_name, tot_goal, tot_assist 
		FROM (
			SELECT blog_player.id, blog_player.player_name, blog_player.fifa_year_id, blog_year.fifa_year
			FROM blog_player
			INNER JOIN blog_year ON blog_player.fifa_year_id = blog_year.id
			WHERE player_team_rec_status = 'A'
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
		order by fifa_year desc, tot_goal desc, player_name
		'''
	
		tot_player_data_query = Year.objects.raw(query_player_tot)

		tot_player_data = []

		for row in tot_player_data_query:
			r = ({"id": row.id, "fifa_year": row.fifa_year, "player": row.player_name, "goals": row.tot_goal, "assists": row.tot_assist})
			tot_player_data.append(r)

		return tot_player_data


class Game(models.Model):
	author_game 			= models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
	#Add fifa year to the player model 9.15.2018
	fifa_year 				= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE)
	tourney_game 			= models.BooleanField(default = False)
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

	def save(self, *args, **kwargs):
	#Converts your_result and opponent_result attribute based on form inputs by 
	#overriding save method of form.

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

	def get_game_data():
	#add method to return game data to populate overall total data display.
	#populates the chartJS

		data = {
		'number_games': [],
		'total_points':[],
		'goals':[],
		'goal_diff':[],
		'number_wins':[],
		'number_ties':[],
		'number_losses':[],
		'manager_name':[],
		'ovr_season_pts':[],
		'GA':[],
		'win_pct':[]
		}

		query = '''
		SELECT data.*, goals - goal_diff GA, seasonpoint.ovr_season_pts from (	
			SELECT id, 
				manager_name
				, rec_status
				, fifa_year
				, sum(total_points) AS total_points
				, sum(goals) AS goals
				, sum(goal_diff) AS goal_diff
				, count(total_points) AS number_games 
				, sum(case when total_points = 3 then 1 end) AS number_wins
				, sum(case when total_points = 1 then 1 end) AS number_ties
				, sum(case when total_points = 0 then 1 end) AS number_losses
				, round(sum(case when total_points = 3 then 1 end) / count(total_points) * 100, 0) win_pct
			FROM (
				SELECT 
					blog_team.id
					, blog_team.manager_name
					, blog_team.rec_status
					, blog_game.fifa_year_id fifa_year
					, blog_game.your_result AS total_points 
					, blog_game.your_score AS goals
					, cast(blog_game.your_score as signed) - cast(blog_game.opponent_score as signed) AS goal_diff
				FROM blog_team LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.your_first_name_id) 

				UNION ALL 

				SELECT 
					blog_team.id
					, blog_team.manager_name
					, blog_team.rec_status
					, blog_game.fifa_year_id fifa_year
					, blog_game.opponent_result AS total_points 
					, blog_game.opponent_score AS goals
					, cast(blog_game.opponent_score as signed) - cast(blog_game.your_score as signed) AS goal_diff
				FROM blog_team LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.opponent_first_name_id)
			) AGGREGATED 
			WHERE rec_status = 'A'
			and fifa_year = (select max(id) from blog_year)
			GROUP BY id, manager_name, rec_status, fifa_year
			) data
		LEFT OUTER JOIN
		(
		select 
			manager_name_id, 
			sum(season_points) ovr_season_pts 
		from blog_seasonpoint 
		where blog_seasonpoint.fifa_year_id = (select max(id) from blog_year)
		GROUP BY manager_name_id
		) seasonpoint ON data.id = seasonpoint.manager_name_id
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
			data['ovr_season_pts'].append(int(info.ovr_season_pts or 0))
			data['GA'].append(int(info.GA or 0))
			data['win_pct'].append(int(info.win_pct or 0)) #adding or 0 prevents NoneType error.
		return data

	def get_season_game_data():
		#This function returns raw SQL to populate the seasons datatable.
		query_season = '''
		SELECT 
			id
			, manager_name
			, season_number
			, fifa_year
			, sum(case when total_points = 3 then 1 else 0 end) AS number_wins
			, sum(case when total_points = 1 then 1 else 0 end) AS number_ties
			, sum(case when total_points = 0 then 1 else 0 end) AS number_losses
			, sum(total_points) AS total_points
			, sum(goals) AS goals
			, sum(goals) - sum(goal_diff) AS GA
			, sum(goal_diff) AS goal_diff
			, count(total_points) AS number_games 

		FROM (
				
			SELECT 
				blog_team.id
				, blog_season.season_number
				, blog_year.fifa_year fifa_year
				, blog_team.manager_name
				, blog_team.rec_status
				, blog_game.your_result AS total_points 
				, blog_game.your_score AS goals
				, cast(blog_game.your_score as signed) - cast(blog_game.opponent_score as signed) AS goal_diff
			FROM blog_team 
			LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.your_first_name_id) 
			LEFT OUTER JOIN blog_season ON (blog_game.season_number_id = blog_season.id)
			LEFT OUTER JOIN blog_year ON (blog_season.fifa_year_id = blog_year.id)
			WHERE blog_team.rec_status = 'A'
			
			UNION ALL 
			
			SELECT 
				blog_team.id
				, blog_season.season_number
				, blog_year.fifa_year fifa_year
				, blog_team.manager_name
				, blog_team.rec_status
				, blog_game.opponent_result AS total_points 
				, blog_game.opponent_score AS goals
				, cast(blog_game.opponent_score as signed) - cast(blog_game.your_score as signed) AS goal_diff
			FROM blog_team 
			LEFT OUTER JOIN blog_game ON (blog_team.id = blog_game.opponent_first_name_id) 
			LEFT OUTER JOIN blog_season ON (blog_game.season_number_id = blog_season.id)
			LEFT OUTER JOIN blog_year ON (blog_season.fifa_year_id = blog_year.id)
			WHERE blog_team.rec_status = 'A'
			) AGGREGATED 
		WHERE season_number is not null
		GROUP BY id, manager_name, rec_status, season_number, fifa_year
		ORDER BY SEASON_NUMBER
		'''

		seasonal_data = Team.objects.raw(query_season)

		rows = []
		for row in seasonal_data:
			r = ({"fifa_year": str(row.fifa_year), "season":"Season " + str(row.season_number), "manager": row.manager_name, "wins": row.number_wins, "ties": row.number_ties, "losses": row.number_losses
				, "points": row.total_points, "goals": row.goals, "GA": row.GA, "GD": row.goal_diff, "games": row.number_games})
			rows.append(r)


		return rows

	def get_headtohead_data():
		#This function returns raw SQL to populate the head to head games datatable.
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
		, round(sum(number_wins) / count(result) * 100, 0) win_pct
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
			where blog_game.season_number_id in (select blog_season.id from blog_season where special_season_ind <> 1)
			and blog_game.fifa_year_id = (select max(bg.fifa_year_id) from blog_game bg)
			and blog_game.tourney_game = 0

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
			where blog_game.season_number_id in (select blog_season.id from blog_season where special_season_ind <> 1)
			and blog_game.fifa_year_id = (select max(bg.fifa_year_id) from blog_game bg)
			and blog_game.tourney_game = 0
			) stats
		group by stats.player, stats.opponent
		'''

		headtohead_data = Game.objects.raw(query_headtohead)

		rows = []
		for row in headtohead_data:
			r = ({"player": row.id, "opponent": row.opponent, "wins": row.wins, "ties": row.ties, "losses": row.losses
				, "points": row.total_points, "GD": row.GD, "games": row.games, "win_pct": row.win_pct})
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
	fifa_year 	= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE)
	game 		= models.ForeignKey(Game, default = get_default_game_number, on_delete = models.CASCADE)
	num_goals 	= models.PositiveIntegerField(null = True)

	def __str__(self):
		return '{} {}'.format("Game",self.game) 


	def get_goal_against_data():
		#This function returns raw SQL to populate the head to head players datatable.
		query_player = '''
		SELECT goals.*, tot_assists from (
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
					and blog_player.fifa_year_id = (select max(bp.fifa_year_id) from blog_player bp)
					) data1
				INNER JOIN 
				blog_team ON data1.opponent = blog_team.id
				WHERE opponent is not null
				GROUP BY id, mgr, player, opponent_scored_on
				ORDER BY player, mgr, tot_goals
				) goals
			
			LEFT JOIN
			
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
					and blog_player.fifa_year_id = (select max(bp.fifa_year_id) from blog_player bp)
					) data1
				INNER JOIN 
				blog_team ON data1.opponent = blog_team.id
				WHERE opponent is not null
				GROUP BY player,opponent_scored_on
				ORDER BY player
				) assists
			ON goals.player = assists.player
			AND goals.opponent_scored_on = assists.opponent_scored_on
		
		UNION ALL
		
		SELECT assists2.id, assists2.mgr, assists2.player, assists2.opponent_scored_on, goals2.tot_goals, assists2.tot_assists 
		FROM (
			SELECT id, mgr, player, blog_team.manager_name opponent_scored_on, sum(num_assists) tot_assists FROM (
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
				and blog_player.fifa_year_id = (select max(bp.fifa_year_id) from blog_player bp)
				) data1
			INNER JOIN 
			blog_team ON data1.opponent = blog_team.id
			WHERE opponent is not null
			GROUP BY id, mgr, player, opponent_scored_on
			ORDER BY player
			) assists2
			
			LEFT JOIN
			
			(
			SELECT player, blog_team.manager_name opponent_scored_on, sum(num_goals) tot_goals FROM (
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
				and blog_player.fifa_year_id = (select max(bp.fifa_year_id) from blog_player bp)
				) data1
			INNER JOIN 
			blog_team ON data1.opponent = blog_team.id
			WHERE opponent is not null
			GROUP BY player, opponent_scored_on
			ORDER BY player, tot_goals
			) goals2
			
		ON assists2.player = goals2.player
		AND assists2.opponent_scored_on = goals2.opponent_scored_on
		WHERE tot_goals is NULL
	'''
	
		goal_against_data = Player.objects.raw(query_player)

		goal_against_rows = []

		for row in goal_against_data:
			r = ({"id":row.id, "manager": row.mgr, "player": row.player, "mgr": row.opponent_scored_on, "goals": row.tot_goals, "assists": row.tot_assists})
			goal_against_rows.append(r)


		return goal_against_rows

class Assist(models.Model):
	player_name = models.ForeignKey(Player, on_delete = models.CASCADE)
	fifa_year 	= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE)
	game 		= models.ForeignKey(Game, default = get_default_game_number, on_delete = models.CASCADE)
	num_assists = models.PositiveIntegerField(null = True)

	def __str__(self):
		return '{} {}'.format("Assist",self.game) 


class SeasonPoint(models.Model):
	manager_name 	= models.ForeignKey(Team, on_delete = models.CASCADE)
	season_points 	= models.PositiveIntegerField()
	#Add fifa year to the player model 9.15.2018
	fifa_year 		= models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE)
	season_number 	= models.ForeignKey(Season,  default = get_default_season_number, on_delete = models.CASCADE) 


	def __str__(self):
		return '{} {}'.format("Season Point",self.manager_name) 




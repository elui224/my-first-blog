
import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max, Sum, Count
from django.db.models import signals
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from markdown_deux import markdown
from PIL import Image



class PostManager(models.Manager):
	def active(self, *args, **kwargs):
		return super(PostManager, self).filter(draft=False).filter(publish_date__lte=timezone.now()).order_by('-created_date')


def img_upload_location(instance, filename):
	return "%s/%s" %(instance.slug, filename)

class Post(models.Model):
	author = models.ForeignKey('auth.User')
	title = models.CharField(max_length = 100)
	draft = models.BooleanField(default = False)
	slug = models.SlugField(unique = True)
	image = models.ImageField(upload_to=img_upload_location,
		null = True,
		blank = True, 
		height_field = "height_field", 
		width_field = "width_field")
	height_field = models.IntegerField(default=0, null=True, blank = True)
	width_field = models.IntegerField(default=0, null=True, blank = True)
	bodytext = models.TextField()
	created_date = models.DateTimeField(default = timezone.now)
	publish_date = models.DateTimeField(auto_now = False, auto_now_add = False)

	objects = PostManager()

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


def create_slug(instance, new_slug=None): #recursive function to check whether instance of pk exists to create file name for post.
	slug = slugify(instance.title)
	if new_slug is not None:
		slug = new_slug
	qs = Post.objects.filter(slug=slug).order_by("-pk")
	exists = qs.exists()
	if exists:
		new_slug = "%s-%s" %(slug, qs.first().pk)
		return create_slug(instance, new_slug=new_slug)
	return slug

def pre_save_post_receiver(sender, instance, *args, **kwargs): #creates a new slug for a post before saving.
	if not instance.slug:
		instance.slug = create_slug(instance)

pre_save.connect(pre_save_post_receiver, sender=Post)


class Team(models.Model):
	manager_name = models.CharField(max_length = 50)
	ACTIVE = 'A'
	INACTIVE = 'I'
	STATUS_CHOICES = (
		(ACTIVE, 'Active'),
		(INACTIVE, 'Inactive')
		)
	rec_status = models.CharField(max_length = 1, default = ACTIVE, choices = STATUS_CHOICES)

	def __str__(self):
		return self.manager_name

	def get_active_teams():
		active_teams = Team.objects.filter(rec_status='A').values_list('manager_name', flat = True)
		return active_teams

	def get_active_teams_count():
		active_teams_count = Team.objects.filter(rec_status='A').count()
		return active_teams_count



class Player(models.Model):
	team = models.ForeignKey(Team, on_delete = models.CASCADE) #Each player can belong to multiple teams as they get traded.
	player_name = models.CharField(max_length = 100)

	def __str__(self):
		return str(self.player_name)

	class Meta:
		ordering = ('player_name',)



class Year(models.Model):
	fifa_year = models.PositiveIntegerField(default=1)
	def __str__(self):
		return '{} {}'.format('Fifa Year', self.fifa_year)

def get_current_year_number():
	year_qs = Year.objects.all()
	year_exists = year_qs.exists()
	if year_exists:
		current_year_object = Year.objects.latest('fifa_year')
		now = timezone.now()
		fifa_release_date = datetime.date(day=26, year=2017, month=9)  #release date of fifa18. Setting release date needs work.
		if now == fifa_release_date:
			current_fifa_year = Year.objects.all().aggregate(Max('fifa_year'))['fifa_year__max']
			next_fifa_year = current_fifa_year + 1
			Year.objects.create(fifa_year=next_fifa_year)
			current_year_object = Year.objects.latest('fifa_year')
	else:
		current_year_object = Year.objects.create(fifa_year=1)
	return current_year_object



class Season(models.Model):
	fifa_year = models.ForeignKey(Year, null=True, default = get_current_year_number, on_delete = models.CASCADE) 
	season_number = models.PositiveIntegerField()

	def __str__(self):
		return '{} {}'.format('Season', self.season_number)


#Returns the current season based on number of games played to display.
def get_default_season_number(): 
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
	season_number = models.ForeignKey(Season, null = True,  default = get_default_season_number, on_delete = models.CASCADE) 
	your_first_name = models.ForeignKey(Team, on_delete = models.CASCADE, related_name = 'your_first_name')
	opponent_first_name = models.ForeignKey(Team, on_delete = models.CASCADE, related_name = 'opponent_first_name')
	your_score = models.PositiveIntegerField()
	opponent_score = models.PositiveIntegerField()
	your_result = models.PositiveIntegerField(editable=False)
	opponent_result = models.PositiveIntegerField(editable=False)
	timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)
	updated = models.DateTimeField(auto_now_add=False, auto_now=True)	

	def __str__(self):
		return '{} vs {}'.format(self.your_first_name.manager_name, self.opponent_first_name.manager_name) 


	def save(self, *args, **kwargs):
		# if self.pk is None and not self.season_number:
		# 	self.season_number = 1
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

	def get_player_data():
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
			, count(case when total_points = 3 then 'W' end) AS number_wins
			, count(case when total_points = 1 then 'W' end) AS number_ties
			, count(case when total_points = 0 then 'W' end) AS number_losses
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
			data['total_points'].append(int(info.total_points))
			data['goals'].append(int(info.goals))
			data['goal_diff'].append(int(info.goal_diff))
			data['number_games'].append(info.number_games)
			data['number_wins'].append(info.number_wins)
			data['number_ties'].append(info.number_ties)
			data['number_losses'].append(info.number_losses)

		return data


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
	game = models.ForeignKey(Game, default = get_default_game_number, on_delete = models.CASCADE)
	num_goals = models.PositiveIntegerField(null = True)

	def __str__(self):
		return '{} {}'.format("Game",self.game) 




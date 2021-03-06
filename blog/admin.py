from django.contrib import admin
from .models import Post, Team, Player, Year, Season, Game, Goal, Assist, SeasonPoint


# This customizes the admin panel.
class PostModelAdmin(admin.ModelAdmin):
	list_display = ["title","created_date"]
	list_filter = ["created_date"]
	search_fields = ["title","bodytext"]
	
	class Meta:
		model = Post

class TeamModelAdmin(admin.ModelAdmin):
	list_display = ["manager_name","rec_status"]

	class Meta:
		model = Team

class PlayerModelAdmin(admin.ModelAdmin):
	list_display = ["player_name", "team", "fifa_year"]
	list_filter = ["team"]
	search_fields = ["player_name","team__manager_name"]

	class Meta:
		model = Player

class YearModelAdmin(admin.ModelAdmin):
	list_display = ["fifa_year"]
	list_filter = ["fifa_year"]

	class Meta:
		model = Year

class SeasonModelAdmin(admin.ModelAdmin):
	list_display = ["season_number", "fifa_year",]
	list_filter = ["season_number", "fifa_year",]

	class Meta:
		model = Season

class GameModelAdmin(admin.ModelAdmin):
	list_display = ["your_first_name","opponent_first_name","your_score","opponent_score",
		"season_number","timestamp","author_game", "fifa_year",]
	list_filter = ["timestamp", "your_first_name", "opponent_first_name",]
	search_fields = ["season_number__season_number", "fifa_year",]

	class Meta:
		model = Game

class GoalModelAdmin(admin.ModelAdmin):
	list_display = ["player_name","game","num_goals"]
	search_fields = ["player_name__player_name"]

	class Meta:
		model = Goal

class AssistModelAdmin(admin.ModelAdmin):
	list_display = ["player_name","game","num_assists"]
	search_fields = ["player_name__player_name"]

	class Meta:
		model = Assist

class SeasonPointModelAdmin(admin.ModelAdmin):
	list_display = ["manager_name","season_points","season_number"]
	search_fields = ["season_number"]

	class Meta:
		model = SeasonPoint


admin.site.register(Post, PostModelAdmin)
admin.site.register(Team, TeamModelAdmin)
admin.site.register(Player, PlayerModelAdmin)
admin.site.register(Year, YearModelAdmin)
admin.site.register(Season, SeasonModelAdmin)
admin.site.register(Game, GameModelAdmin)
admin.site.register(Goal, GoalModelAdmin)
admin.site.register(Assist, AssistModelAdmin)
admin.site.register(SeasonPoint, SeasonPointModelAdmin)



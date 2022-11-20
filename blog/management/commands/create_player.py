import os, csv

from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from blog.models import Player, Team, Year

CURRENT_FIFA_YEAR = date.today().year + 1

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open(os.path.join(settings.BASE_DIR, f'blog/file_import/players/drafted_players_{CURRENT_FIFA_YEAR}.csv'), 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    Player.objects.create(
                        fifa_year=Year.objects.get(fifa_year=CURRENT_FIFA_YEAR),
                        team=Team.objects.get(manager_name=row['team']),
                        player_name=row['player_name'],     
                        player_team_rec_status='A',
                    )
                except:
                    raise CommandError(f"Unable to add {row['player_name']} to {row['team']} for {CURRENT_FIFA_YEAR}")
                self.stdout.write(self.style.SUCCESS(f"Successfully saved {row['player_name']} to {row['team']} for {CURRENT_FIFA_YEAR}!"))
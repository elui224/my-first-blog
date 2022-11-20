import os, csv

from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from blog.models import Player, Team, Year

from optparse import make_option

CURRENT_FIFA_YEAR = date.today().year + 1

class Command(BaseCommand):
    '''
    Run command using python manage.py create_player --file=path/to/myfile.csv.
    For example, python manage.py create_player --file=./blog/file_import/players/drafted_players_2023.csv
    '''

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--file', type=str, help="file path")

    def handle(self, *args, **options):
        file_path = options['file']
        if file_path == None :
            raise CommandError("Option `--file=...` must be specified.")

        if not os.path.isfile(file_path) :
            raise CommandError("File does not exist at the specified path.")

        with open(file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    p, created_player = Player.objects.get_or_create( #Use to avoid dupes. Get or replace returns tuple, indicating whether we're getting or creating based on inputs.
                        fifa_year=Year.objects.get(fifa_year=CURRENT_FIFA_YEAR),
                        team=Team.objects.get(manager_name=row['team']),
                        player_name=row['player_name'],     
                        player_team_rec_status='A',
                    )
                except:
                    raise CommandError(f"Unable to add {row['player_name']} to {row['team']} for {CURRENT_FIFA_YEAR}")
                if created_player:
                    self.stdout.write(self.style.SUCCESS(f"Successfully saved {row['player_name']} to Team {row['team']} for {CURRENT_FIFA_YEAR}!"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Checked {row['player_name']} on Team {row['team']} for {CURRENT_FIFA_YEAR} and no changes are needed."))
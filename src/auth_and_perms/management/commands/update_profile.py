from django.contrib.auth.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Load permission category'

    def ask_confirmation(self):
        yes_choices = ['yes', 'y']
        no_choices = ['no', 'n']
        continue_while = True
        while continue_while:
            user_input = input('Do you want to continue? yes/no: ')

            if user_input.lower() in yes_choices:
                return True
            elif user_input.lower() in no_choices:
                return False
            else:
                print('Type yes/no')

    def clean_userpass(self):
        for user in User.objects.all():
            user.set_password('Admin12345')
            user.save()

    def handle(self, *args, **options):
        if self.ask_confirmation():
            self.clean_userpass()


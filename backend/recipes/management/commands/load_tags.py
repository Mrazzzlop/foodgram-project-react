"""
Команда для импота тэгов в БД.
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Tag


class Command(BaseCommand):
    """Команда импотра Тэгов в базу данных"""
    help = 'Импорт тэгов из файла json'

    BASE_DIR = settings.BASE_DIR

    def handle(self, *args, **options):
        try:
            path = self.BASE_DIR / 'data/tags.json'
            with open(path, 'r', encoding='utf-8-sig') as file:
                data = json.load(file)
                for item in data:
                    Tag.objects.get_or_create(**item)
                    self.stdout.write(f'add {item}')
        except CommandError as error:
            raise CommandError from error

        self.stdout.write(self.style.SUCCESS('Данные успешно загружены'))

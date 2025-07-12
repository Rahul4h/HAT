
from django.core.management.base import BaseCommand
from app.models import Recommendation, Product
from django.contrib.auth.models import User
import csv

class Command(BaseCommand):
    help = 'Imports recommendations from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the recommendations.csv file')

    def handle(self, *args, **options):
        file_path = options['csv_file']

        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # skip header

            count = 0
            for row in reader:
                try:
                    user_id, product_id = map(int, row)
                    user = User.objects.get(id=user_id)
                    product = Product.objects.get(id=product_id)
                    Recommendation.objects.get_or_create(user=user, product=product)
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Skipped row {row}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} recommendations'))


from django.core.management.base import BaseCommand
from app.models import Order, OrderItem
import csv
import os

class Command(BaseCommand):
    help = 'Exports order data for Market Basket Analysis'

    def handle(self, *args, **kwargs):
        output_file = 'order_data.csv'

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user_id', 'product_id'])

            orders = Order.objects.prefetch_related('items__product')
            for order in orders:
                for item in order.items.all():
                    writer.writerow([order.user.id, item.product.id])

        self.stdout.write(self.style.SUCCESS(f'Data exported to {output_file}'))

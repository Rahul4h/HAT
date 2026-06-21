from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Blogs


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(stock__gt=0)  # যেগুলো স্টকে আছে সেগুলোই

    def location(self, obj):
        return reverse('product_detail', args=[obj.id])


class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Blogs.objects.all()

    def lastmod(self, obj):
        return obj.timeStamp

    def location(self, obj):
        return reverse('blog_detail', args=[obj.id])


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        # Product model এর category field থেকে unique category গুলো নেওয়া
        return Product.objects.values_list('category', flat=True).distinct()

    def location(self, item):
        return reverse('category_products', args=[item])


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ['index', 'about', 'contact', 'handleBlog']

    def location(self, item):
        return reverse(item)
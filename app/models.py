from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
from cloudinary_storage.storage import VideoMediaCloudinaryStorage

#from .models import Product
# Create your models here.
class Contact(models.Model):
    name=models.CharField(max_length=30)
    email=models.EmailField()
    phoneNumber=models.CharField(max_length=12)
    description=models.TextField()
    def __str__(self):
        return f'Message from {self.name}'
    

# models.py
from django.db import models

class Blogs(models.Model):
    
    CATEGORY_CHOICES = [
        ('shirt', 'Shirt'),
        ('t-shirt', 'T-shirt'),
        ('saree', 'Saree'),
        ('shoes', 'Shoes'),
        ('jeans', 'Jeans'),
        ('fans', 'Fans'),
        ('toys', 'Toys'),
        ('cake', 'Cake'),
        ('dryfruits', 'Dryfruits'),
        ('ear-phone', 'Ear-phone'),
        ('laptop', 'Laptop'),
        ('car', 'Car'),
        ('frame', 'Frame'),
        # Add more as needed
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    img = models.ImageField(upload_to='blog_images/')
    authname = models.CharField(max_length=50,db_index=True)
    timeStamp = models.DateTimeField(auto_now_add=True, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='shirt', db_index=True)
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='blogs'
    )

    def __str__(self):
        return self.title
    
    class Meta:
        indexes=[models.Index(fields=['category' , 'timeStamp'])]

    

class Message(models.Model):
    sender = models.ForeignKey(User,on_delete=models.CASCADE,related_name='sent_messages',db_index=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', db_index=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    def __str__(self):
        return f'{self.sender}-{self.receiver}:{self.content[:20]}'
    
    class Meta:
        indexes=[models.Index(fields=['sender', 'receiver']),
                 models.Index(fields=['sender', 'timestamp']),
                 models.Index(fields=['receiver','timestamp'])]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(choices=[('salesman', 'Salesman'), ('customer', 'Customer')], max_length=10,db_index=True)




class Product(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Uncategorized', db_index=True)
    image = models.ImageField(upload_to='products/')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    stock = models.PositiveIntegerField(default=0, db_index=True)
    piece = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(
        'DeliveryBoy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_products',
    )

    @property
    def shop_name(self):

        if self.uploaded_by:
            username = self.uploaded_by.user.username.capitalize()
            shop_id = self.uploaded_by.id

            return f"HAT's Store #{shop_id}"

        return "HAT Official Store"

    def __str__(self):
        return self.title
    class Meta:
        indexes=[models.Index(fields=['category', 'sale_price']),
                 models.Index(fields=['category', 'stock']),]
    


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"
    
    class Meta:
        indexes=[models.Index(fields=['user', 'product'])]

class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments',db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.username} on {self.product.title}"
    
    class Meta:
      indexes = [
        models.Index(fields=['product', 'created_at']),
    ]
    

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    address = models.TextField()
    
    phone = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^\d{1,11}$',
                message='Phone number must be numeric and up to 11 digits.'
            )
        ], db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.address}"

    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    address = models.TextField()  # Optional: You may remove this if you always use shipping_address
    payment_method = models.CharField(max_length=20, db_index=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_cancelled = models.BooleanField(default=False, db_index=True)
    # in Order model
    
    delivery_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('assigned', 'Assigned'), ('delivered', 'Delivered')],
        default='pending', db_index=True)


    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    class Meta:
     indexes = [
        models.Index(fields=['user', 'created_at']),
        models.Index(fields=['user', 'delivery_status']),
        models.Index(fields=['delivery_status', 'created_at']),
    ]

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"
    


class ChatMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_sent_messages'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_received_messages'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username} at {self.timestamp}"



class DeliveryBoy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^\d{1,11}$',
                message='Phone number must be exactly 11 digits.'
            )
        ]
    )

    address = models.TextField(blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} (Delivery Boy)'

    







class DeliveryOrder(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_info')  # NEW: Link to original Order
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_orders",db_index=True)
    assigned_to = models.ForeignKey(DeliveryBoy, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_orders", db_index=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('assigned', 'Assigned'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending',db_index=True)
    address = models.TextField()
    total = models.FloatField(default=0)
    payment_method = models.CharField(max_length=50, default='Cash')
    order_image = models.ImageField(upload_to='orders/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_cancelled = models.BooleanField(default=False)
    marked_delivered_by_boy = models.BooleanField(default=False)
    confirmed_by_customer = models.BooleanField(default=False)

    def __str__(self):
        return f"Delivery for Order #{self.order.id} by {self.user.username}"

    class Meta:
      indexes = [
        models.Index(fields=['status', 'created_at']),
        models.Index(fields=['assigned_to', 'status']),
    ]



class ReturnRequest(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='return_request'

    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    reason = models.TextField()

    assigned_to = models.ForeignKey(
        DeliveryBoy,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    video = models.FileField(
        upload_to='returns/videos/',
        storage=VideoMediaCloudinaryStorage() if settings.USE_CLOUDINARY else None,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    is_collected = models.BooleanField(default=False)

    collected_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('assigned', 'Assigned'),
            ('collected', 'Collected'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    def __str__(self):
        return f"Return #{self.id} for Order #{self.order.id}"

    class Meta:
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
from django.db import models

class ProductRecommendation(models.Model):
    base_product = models.ForeignKey('Product', related_name='base_product', on_delete=models.CASCADE)
    recommended_product = models.ForeignKey('Product', related_name='recommended_product', on_delete=models.CASCADE)
    confidence = models.FloatField()

    def __str__(self):
        return f"{self.base_product.title} ➤ {self.recommended_product.title} ({self.confidence:.2f})"

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('user', 'product')
        indexes = [
        models.Index(fields=['user', 'timestamp']),
        models.Index(fields=['product', 'timestamp']),
    ]  # Prevent duplicates

    def __str__(self):
        return f'Recommendation: {self.user.username} → {self.product.title}'
    

class BlogImage(models.Model):

    blog = models.ForeignKey(
        Blogs,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='blog_images/'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return self.blog.title

  

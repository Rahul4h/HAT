from django.contrib import admin
from app.models import Contact,Blogs,Product,Profile,CartItem,Comment,ShippingAddress,Order,OrderItem,ChatMessage, DeliveryBoy,DeliveryOrder,ReturnRequest,BlogImage
# Register your models here.

admin.site.register(Contact)
admin.site.register(Blogs)
admin.site.register(Product)
admin.site.register(Profile)
admin.site.register(CartItem)
admin.site.register(Comment)
admin.site.register(ShippingAddress)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ChatMessage)
admin.site.register(BlogImage)

@admin.register(DeliveryBoy)
class DeliveryBoyAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'joined_at')
    search_fields = ('user__username', 'phone')



@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'assigned_to', 'is_delivered_display', 'created_at')
    list_filter = ('status', 'created_at')  # ✅ 'status' is a valid model field
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)

    def is_delivered_display(self, obj):
        return obj.status == 'delivered'
    is_delivered_display.boolean = True
    is_delivered_display.short_description = 'Delivered?'








@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'customer',
        'amount',
        'status',
        'assigned_to',
        'created_at',
        'is_collected',
    )

    list_filter = (
        'status',
        'is_collected',
        'created_at',
    )

    search_fields = (
        'order__id',
        'customer__username',
    )

    readonly_fields = (
        'created_at',
        'collected_at',
    )

    fieldsets = (
        ('Return Information', {
            'fields': (
                'order',
                'customer',
                'amount',
                'reason',
                'video',
            )
        }),

        ('Assignment', {
            'fields': (
                'assigned_to',
                'status',
            )
        }),

        ('Collection Status', {
            'fields': (
                'is_collected',
                'collected_at',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
            )
        }),
    )






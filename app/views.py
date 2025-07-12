#from email import message
from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout

from .forms import CommentForm,ShippingAddressForm
from .models import Contact,Blogs,Product,Profile,CartItem,Comment,ShippingAddress,Order,OrderItem,ChatMessage,DeliveryBoy,DeliveryOrder,ReturnRequest,Recommendation
from django.conf import settings
#from django.core.mail import send_mail
from django.core import mail
from django.core.mail import send_mail
from django.core.mail.message import EmailMessage
from django.contrib.auth.decorators import login_required
import requests
from django.http import JsonResponse,HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q,F, ExpressionWrapper, FloatField, Max
from django.forms import modelform_factory,inlineformset_factory
from django.utils import timezone


  



# Create your views here.


def index(request):
    # Flash Sale Products
    products_with_discount = Product.objects.annotate(
        discount_percentage=ExpressionWrapper(
            (F('original_price') - F('sale_price')) * 100 / F('original_price'),
            output_field=FloatField()
        )
    ).filter(original_price__gt=F('sale_price'))

    category_map = {}
    for product in products_with_discount:
        cat = product.category
        if cat not in category_map or product.discount_percentage > category_map[cat].discount_percentage:
            category_map[cat] = product
    flash_sale_products = list(category_map.values())

    # All products
    all_products = Product.objects.annotate(
        discount_percentage=ExpressionWrapper(
            (F('original_price') - F('sale_price')) * 100 / F('original_price'),
            output_field=FloatField()
        )
    ).order_by('-id')[:30]

    # 🔽 "Only for You" logic (Market Basket Recommendations)
    only_for_you = []
    if request.user.is_authenticated:
        from .models import OrderItem
        # Get product IDs the user already bought
        
        user_product_ids = OrderItem.objects.filter(order__user=request.user).values_list('product_id', flat=True)

        # Find recommendations for those products
        recommended_ids = Recommendation.objects.filter(
        user=request.user,
        product_id__in=user_product_ids,
        
        ).values_list('product_id', flat=True).distinct()

        only_for_you = Product.objects.filter(id__in=recommended_ids)[:10]


    return render(request, 'index.html', {
        'flash_sale_products': flash_sale_products,
        'products': all_products,
        'only_for_you': only_for_you  # ✅ add to context
    })




def about(request):
    return render(request, 'about.html')



@login_required
def contact(request):
    admin_user = User.objects.filter(is_superuser=True).first()  # Get admin

    # Get existing chat messages
    chat_messages = ChatMessage.objects.filter(
        sender=request.user, recipient=admin_user
    ) | ChatMessage.objects.filter(
        sender=admin_user, recipient=request.user
    )
    chat_messages = chat_messages.order_by('timestamp')

    # Handle both contact form and chat message
    if request.method == "POST":
        # Case 1: User submitted chat message (not contact form)
        if request.POST.get("message"):
            ChatMessage.objects.create(
                sender=request.user,
                recipient=admin_user,
                message=request.POST.get("message")
            )
            return redirect('/contact')

        # Case 2: User submitted contact form
        fname = request.POST.get("name")
        femail = request.POST.get("email")
        phone = request.POST.get("phone")
        desc = request.POST.get("desc")

        query = Contact(name=fname, email=femail, phoneNumber=phone, description=desc)
        query.save()

        # Send email
        from_email = settings.EMAIL_HOST_USER
        connection = mail.get_connection()
        connection.open()

        email_message = mail.EmailMessage(
            f'Email from {fname}',
            f'UserEmail: {femail} \nUserPhoneNumber :{phone}\n\n\nQuery:{desc}',
            from_email,
            ['rahul17@cse.pstu.ac.bd'],
            connection=connection
        )

        email_client = mail.EmailMessage(
            'Admin Response',
            'Thanks for reaching us\n\n  HAT',
            from_email,
            [femail],
            connection=connection
        )

        connection.send_messages([email_message, email_client])
        connection.close()

        messages.info(request, "Thanks for contacting us, we will respond soon....")
        return redirect('/contact')

    return render(request, 'contact.html', {'chat_messages': chat_messages})
    


def handlelogin(request):
    if request.method=="POST":
        uname=request.POST.get("username")
        pass1=request.POST.get("pass1")
        myuser=authenticate(username=uname,password=pass1)
        if myuser is not None:
            login(request,myuser)
            messages.success(request,"login success")
            return redirect('/')
        else:
            messages.error(request,"invalid")
            return redirect('/login')
    return render(request,'login.html')

   

   


from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator

def handlesignup(request):
    if request.method == "POST":
        uname = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("pass1")
        confirmpassword = request.POST.get("pass2")

        # Basic empty check
        if not uname or not email or not password or not confirmpassword:
            messages.error(request, "All fields are required.")
            return redirect('handlesignup')

        if password != confirmpassword:
            messages.warning(request, "Passwords do not match")
            return redirect('handlesignup')

        if User.objects.filter(username=uname,is_active=True).exists():
            messages.info(request, "Username is already taken")
            return redirect('handlesignup')

        if User.objects.filter(email=email,is_active=True).exists():
            messages.info(request, "Email is already registered")
            return redirect('handlesignup')

        # Create inactive user
        user = User.objects.create_user(username=uname, email=email, password=password)
        user.is_active = False
        user.save()

        # Send activation email
        current_site = get_current_site(request)
        subject = "Activate Your HAT Account"
        message = render_to_string('activate_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            messages.success(request, "Please check your email to activate your account.")
        except Exception as e:
            messages.error(request, "Error sending activation email. Please try again.")
            user.delete()  # Clean up created user
            return redirect('handlesignup')

        return redirect('handlelogin')
    
    return render(request, 'signup.html')


def activate(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Email confirmed successfully! You can now login.')
        return redirect('handlelogin')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('handlesignup')




def handlelogout(request):
    logout(request)
    messages.info(request,"logout success")
    return redirect('/login')



def handleBlog(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to access the blog section.")
        return redirect('handlelogin')  # replace with your login URL name

    category = request.GET.get('category')
    if category:
        allPosts = Blogs.objects.filter(category__iexact=category)
    else:
        allPosts = Blogs.objects.all()

    context = {
        'allPosts': allPosts,
        'active_category': category
    }
    return render(request, 'blog.html', context)


def search(request):
    query = request.GET.get('search', '').strip()

    if not query or len(query) > 100:
        allPosts = Blogs.objects.none()
        messages.warning(request, "Invalid search query.")
    else:
        title_results = Blogs.objects.filter(title__icontains=query)
        desc_results = Blogs.objects.filter(description__icontains=query)
        allPosts = title_results.union(desc_results)

        if not allPosts.exists():
            messages.info(request, "No search results found.")

    context = {
        'allPosts': allPosts,
        'query': query
    }
    return render(request, 'search.html', context)


#def service(request):
   # return render(request, 'service.html')

@login_required
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    comments = Comment.objects.filter(product=product, parent=None).order_by('-created_at')  # Only parent comments

    can_comment = True  # You can modify this to check if user purchased the product

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            parent_id = form.cleaned_data.get('parent')  # From the hidden input
            comment = form.save(commit=False)
            comment.product = product
            comment.user = request.user

            if parent_id:
                comment.parent = parent_id  # Set parent if it's a reply

            comment.save()
            return redirect('product_detail', id=product.id)
    else:
        form = CommentForm()

    context = {
        'product': product,
        'comments': comments,
        'form': form,
        'can_comment': can_comment,
    }
    return render(request, 'product_detail.html', context)



@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return redirect('product_detail', id=product_id)


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Calculate total amount
    total_amount = 0
    for item in cart_items:
        total_amount += item.product.sale_price * item.quantity

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, 'cart.html', context)



@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Quantity updated.")
        else:
            cart_item.delete()
            messages.info(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')



import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem, ShippingAddress
from .forms import ShippingAddressForm

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    delivery_fee = 30
    subtotal = product.sale_price * quantity
    total = subtotal + delivery_fee

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        payment_method = request.POST.get('payment_method')

        if form.is_valid() and payment_method in ['stripe', 'cod']:
            if product.stock < quantity:
                messages.error(request, f"Sorry, only {product.stock} item(s) left in stock.")
                return redirect('checkout', product_id=product.id)

            shipping = form.save(commit=False)
            shipping.user = request.user
            shipping.save()

            if payment_method == 'stripe':
                request.session['shipping_id'] = shipping.id
                request.session['product_id'] = product.id
                request.session['quantity'] = quantity

                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'bdt',
                            'unit_amount': int(product.sale_price * 100),
                            'product_data': {
                                'name': product.title,
                            },
                        },
                        'quantity': quantity,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri('/checkout/success/'),
                    cancel_url=request.build_absolute_uri('/checkout/cancel/'),
                )
                return JsonResponse({'session_url': session.url})

            # Cash on Delivery processing
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping,
                address=shipping.address,
                payment_method='cod',
                total=total
            )
            OrderItem.objects.create(order=order, product=product, quantity=quantity)
            product.stock -= quantity
            product.save()

            send_mail(
                subject="Your Order Confirmation",
                message=f"Thank you for your order #{order.id}!\n\nProduct: {product.title}\nQuantity: {quantity}\nTotal: ৳{total}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            return render(request, 'order_confirmation.html', {
                'product': product,
                'quantity': quantity,
                'total': total,
                'payment_method': 'cod',
                'shipping': shipping,
                'message': "✅ Your order has been placed with Cash on Delivery!",
                'order_id': order.id
            })

    else:
        form = ShippingAddressForm()

    context = {
        'product': product,
        'quantity': quantity,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'form': form
    }
    return render(request, 'checkout.html', context)

@login_required
def stripe_success(request):
    shipping_id = request.session.get('shipping_id')
    product_id = request.session.get('product_id')
    quantity = int(request.session.get('quantity', 1))

    shipping = get_object_or_404(ShippingAddress, id=shipping_id)
    product = get_object_or_404(Product, id=product_id)
    delivery_fee = 30
    subtotal = product.sale_price * quantity
    total = subtotal + delivery_fee

    # Confirm stock again (very important!)
    if product.stock < quantity:
        messages.error(request, f"Sorry, the product is out of stock.")
        return redirect('checkout', product_id=product.id)

    order = Order.objects.create(
        user=request.user,
        shipping_address=shipping,
        address=shipping.address,
        payment_method='stripe',
        total=total
    )
    OrderItem.objects.create(order=order, product=product, quantity=quantity)
    product.stock -= quantity
    product.save()

    send_mail(
        subject="Your Stripe Order Confirmation",
        message=f"Thanks for paying via Stripe!\n\nOrder #{order.id}\nProduct: {product.title}\nQuantity: {quantity}\nTotal: ৳{total}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.user.email],
        fail_silently=False,
    )

    return render(request, 'order_confirmation.html', {
        'product': product,
        'quantity': quantity,
        'total': total,
        'payment_method': 'stripe',
        'shipping': shipping,
        'message': "✅ Your payment was successful via Stripe!",
        'order_id': order.id
    })

@login_required
def stripe_cancel(request):
    return render(request, 'cancel.html')




def initiate_sslcommerz_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        product_id = request.POST.get('product_id')

        if not amount or not product_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        data = {
            'store_id': 'mysho685f94ce8b5f7',
            'store_passwd': 'mysho685f94ce8b5f7@ssl',
            'total_amount': amount,
            'currency': 'BDT',
            'tran_id': 'TEST12345',
            'success_url': request.build_absolute_uri('/payment-success/'),
            'fail_url': request.build_absolute_uri('/payment-fail/'),
            'cancel_url': request.build_absolute_uri('/payment-cancel/'),
            'emi_option': 0,
            'cus_name': request.user.get_full_name(),
            'cus_email': request.user.email,
            'cus_add1': 'Dhaka',
            'cus_city': 'Dhaka',      # << এই লাইন যোগ করুন
            'cus_country': 'Bangladesh',
            'cus_phone': '017XXXXXXXX',
            'shipping_method': 'NO',
            'product_name': 'Test Product',
            'product_category': 'General',
            'product_profile': 'general',
        }

    


     
     

        try:
            response = requests.post('https://sandbox.sslcommerz.com/gwprocess/v4/api.php', data=data)
            response_data = response.json()

            print("🔁 SSLCommerz Response:", response_data)

            if 'GatewayPageURL' in response_data:
                return JsonResponse({'GatewayPageURL': response_data['GatewayPageURL']})
            else:
                return JsonResponse({'error': 'SSLCommerz response invalid', 'details': response_data}, status=500)

        except Exception as e:
            print("💥 Exception:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)





def your_success_view(request):
    # Example: you passed these via session or return URL
    product_id = request.session.get('product_id')
    quantity = request.session.get('quantity', 1)
    total = request.session.get('total', 0)

    if not product_id:
        return render(request, 'order_confirmation.html', {
            'message': 'No order found!',
            'product': None,
            'quantity': 0,
            'total': 0,
        })

    product = get_object_or_404(Product, id=product_id)

    return render(request, 'order_confirmation.html', {
        'message': 'Payment Successful!',
        'product': product,
        'quantity': quantity,
        'total': total,
    })


def your_fail_view(request):
    return HttpResponse("Payment Failed")

def your_cancel_view(request):
    return HttpResponse("Payment Cancelled")

def category_products(request, category_name):
    products = Product.objects.filter(category__iexact=category_name)
    return render(request, 'category_products.html', {
        'category_name': category_name,
        'products': products
    })




@require_POST
@login_required
def reorder(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    CartItem.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': quantity}
    )

    messages.success(request, "Product reordered. Added to cart.")
    return redirect('cart')




def blog_detail(request, blog_id):
    blog = get_object_or_404(Blogs, id=blog_id)
    return render(request, 'blog_detail.html', {'blog': blog})

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    # Restore stock
    for item in order_items:
        product = item.product
        product.stock += item.quantity
        product.save()
        item.delete()  # Delete each order item

    # Delete the order itself if needed
    order.delete()

    messages.warning(request, "Your order has been canceled and stock has been restored.")
    return redirect('order_list')  # Redirect wherever you want





from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order, ReturnRequest, DeliveryOrder  # Adjust import paths as needed

@login_required
def order_list(request):
    # Fetch orders with related products
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')

    # Attach latest return request and calculate extra COD amount
    for order in orders:
        try:
            order.return_request = ReturnRequest.objects.filter(order=order).order_by('-created_at').first()
        except ReturnRequest.DoesNotExist:
            order.return_request = None

        # Calculate extra amount to pay if payment method is COD
        paid_amount = getattr(order, 'amount_paid', 0) or 0
        order.extra_cod_amount = max(0, order.total - paid_amount)

    # Map DeliveryOrder by order.id for quick lookup in template
    delivery_orders = DeliveryOrder.objects.filter(user=request.user, order__in=orders)
    delivery_status_map = {d.order.id: d for d in delivery_orders}

    return render(request, 'order_list.html', {
        'orders': orders,
        'delivery_status_map': delivery_status_map,
    })







from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory, modelform_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Order, OrderItem, ShippingAddress
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY



def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    OrderItemFormSet = inlineformset_factory(
        Order, OrderItem, fields=('quantity',), extra=0
    )
    ShippingForm = modelform_factory(ShippingAddress, fields=('address', 'phone'))

    shipping_instance = ShippingAddress.objects.filter(order=order).first()

    if request.method == 'POST':
        formset = OrderItemFormSet(request.POST, instance=order)
        shipping_form = ShippingForm(request.POST, instance=shipping_instance)
        payment_method = request.POST.get('payment_method')

        if formset.is_valid() and shipping_form.is_valid() and payment_method in ['stripe', 'cod']:
            formset.save()

            # Calculate total price
            total = 0
            delivery_fee = 30
            for item in order.items.all():
                total += item.product.sale_price * item.quantity
            total += delivery_fee
            order.total = total

            # Save shipping address
            shipping_address = shipping_form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.order = order
            shipping_address.save()

            order.shipping_address = shipping_address
            order.address = shipping_address.address
            order.payment_method = payment_method
            order.save()

            if payment_method == 'stripe':
                # Save order id in session if needed later
                request.session['update_order_id'] = order.id

                # Create Stripe Checkout session
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'bdt',
                                'unit_amount': int(total * 100),  # amount in paisa (smallest currency unit)
                                'product_data': {
                                    'name': f"Order #{order.id}",
                                },
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=request.build_absolute_uri('/order/update/success/'),
                    cancel_url=request.build_absolute_uri('/order/update/cancel/'),
                )
                return JsonResponse({'session_url': session.url})

            # For Cash on Delivery
            messages.success(request, "Order updated successfully with Cash on Delivery.")
            return redirect('order_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        formset = OrderItemFormSet(instance=order)
        shipping_form = ShippingForm(instance=shipping_instance)

    return render(request, 'update_order.html', {
        'order': order,
        'formset': formset,
        'shipping_form': shipping_form,
    })

@login_required
def update_order_success(request):
    order_id = request.session.get('update_order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.payment_method = 'stripe'
    order.save()

    send_mail(
        subject="Your Updated Stripe Order Confirmation",
        message=f"Thanks! Order #{order.id} updated and paid successfully.\nTotal: ৳{order.total}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.user.email],
        fail_silently=False,
    )

    messages.success(request, "Order updated and paid via Stripe.")
    return redirect('order_list')


@login_required
def update_order_cancel(request):
    messages.error(request, "Stripe payment was cancelled.")
    return redirect('order_list')



@login_required
def chat_view(request):
    admin_user = User.objects.filter(is_superuser=True).first()
    if request.method == "POST":
        message = request.POST.get("message")
        ChatMessage.objects.create(
            sender=request.user,
            recipient=admin_user,
            message=message
        )
        return redirect('contact')  # ⬅️ redirect to contact page

    messages = ChatMessage.objects.filter(
        sender=request.user, recipient=admin_user
    ) | ChatMessage.objects.filter(
        sender=admin_user, recipient=request.user
    )
    messages = messages.order_by('timestamp')

    return render(request, 'contact.html', {'chat_messages': messages})  # ⬅️ render contact.html



def deliveryboy_login(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            # Check if user is a delivery boy
            if hasattr(user, 'deliveryboy'):
                login(request, user)
                return redirect('deliveryboy_home')
            else:
                return render(request, 'deliveryboy_login.html', {'error': 'Not a registered delivery boy'})
        else:
            return render(request, 'deliveryboy_login.html', {'error': 'Invalid credentials'})

    return render(request, 'deliveryboy_login.html')





from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import DeliveryOrder, ReturnRequest

@login_required
def deliveryboy_home(request):
    # Ensure only delivery boys can access
    if not hasattr(request.user, 'deliveryboy'):
        return redirect('deliveryboy_login')

    deliveryboy = request.user.deliveryboy

    # Unassigned pending deliveries
    pending_deliveries = DeliveryOrder.objects.filter(
        status='pending',
        assigned_to__isnull=True
    )

    # Unassigned pending return requests
    pending_returns = ReturnRequest.objects.filter(
        status='pending',
        assigned_to__isnull=True
    )

    # Assigned deliveries to this delivery boy that are:
    # - marked delivered by boy
    # - but not yet confirmed by the customer
    # OR still assigned and not yet marked as delivered
    my_deliveries = DeliveryOrder.objects.filter(
        assigned_to=deliveryboy
    ).filter(
        Q(status='assigned') |
        Q(marked_delivered_by_boy=True, confirmed_by_customer=False)
    ).order_by('-created_at')

    # Assigned returns to this delivery boy that are not yet collected
    my_returns = ReturnRequest.objects.filter(
        assigned_to=deliveryboy,
        is_collected=False,
        status='assigned'
    ).order_by('-created_at')

    context = {
        'deliveryboy': deliveryboy,
        'pending_deliveries': pending_deliveries,
        'pending_returns': pending_returns,
        'my_deliveries': my_deliveries,
        'my_returns': my_returns,
    }

    return render(request, 'deliveryboy_home.html', context)







import re


def deliveryboy_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        # ❌ Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('deliveryboy_signup')

        # ✅ Validate phone number: only digits and exactly 11 characters
        if not re.fullmatch(r'\d{11}', phone):
            messages.error(request, 'Phone number must be exactly 11 digits and contain only numbers.')
            return redirect('deliveryboy_signup')

        # ✅ Create user and delivery boy entry
        user = User.objects.create_user(username=username, password=password, email=email)
        DeliveryBoy.objects.create(user=user, phone=phone, address=address)

        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('deliveryboy_login')

    return render(request, 'deliveryboy_signup.html')


from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

def deliveryboy_logout(request):
    # log the user out
    auth_logout(request)
    # redirect back to delivery‑boy login
    return redirect('deliveryboy_login')

from django.contrib.auth.decorators import login_required
from django.shortcuts         import redirect, get_object_or_404
from .models                  import DeliveryBoy, Order, ReturnRequest  # adjust imports
from django.contrib           import messages


#from .models import DeliveryOrder  # Ensure you import this

@login_required
def assign_delivery_task(request):
    # Only delivery boys may call this
    if not hasattr(request.user, 'deliveryboy'):
        return redirect('deliveryboy_login')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(DeliveryOrder, id=order_id, status='pending', assigned_to__isnull=True)

        # Assign it
        order.assigned_to = request.user.deliveryboy
        order.status = 'assigned'
        order.save()

        messages.success(request, f'Order #{order.id} assigned for delivery.')
    return redirect('deliveryboy_home')


@login_required
def assign_return_task(request):
    # Only delivery boys may call this
    if not hasattr(request.user, 'deliveryboy'):
        return redirect('deliveryboy_login')

    if request.method == 'POST':
        return_id = request.POST.get('return_id')
        ret        = get_object_or_404(ReturnRequest, id=return_id, status='pending', assigned_to__isnull=True)

        # Assign it
        ret.assigned_to = request.user.deliveryboy
        ret.status      = 'out_for_return'
        ret.save()

        messages.success(request, f'Return request #{ret.id} assigned.')
    return redirect('deliveryboy_tasks')





from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Order, DeliveryOrder

@login_required
def mark_order_delivered(request, delivery_order_id):
    try:
        delivery_boy = request.user.deliveryboy
    except DeliveryBoy.DoesNotExist:
        messages.error(request, "You are not authorized as a delivery boy.")
        return redirect('deliveryboy_login')

    # Get the delivery order by its actual DeliveryOrder ID
    delivery_order = get_object_or_404(DeliveryOrder, id=delivery_order_id)

    # Ensure the delivery boy is assigned to this delivery
    if delivery_order.assigned_to != delivery_boy:
        messages.error(request, "You are not assigned to this delivery.")
        return redirect('deliveryboy_home')

    # Mark as delivered
    delivery_order.marked_delivered_by_boy = True
    delivery_order.status = 'assigned'  # Still assigned until customer confirms
    delivery_order.save()

    messages.success(request, f"Order #{delivery_order.order.id} marked as delivered. Waiting for customer confirmation.")
    return redirect('deliveryboy_home')


@login_required
def confirm_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        delivery_order = order.delivery_info  # Using related_name from OneToOneField
    except DeliveryOrder.DoesNotExist:
        messages.error(request, "No delivery info found for this order.")
        return redirect('order_list')

    if delivery_order.marked_delivered_by_boy and not delivery_order.confirmed_by_customer:
        delivery_order.confirmed_by_customer = True
        delivery_order.status = 'delivered'
        delivery_order.save()

        # Update order status too
        order.delivery_status = 'delivered'
        order.save()

        messages.success(request, "Thank you for confirming delivery.")
    else:
        messages.warning(request, "Delivery not yet marked or already confirmed.")

    return redirect('order_list')



from .models import ReturnRequest

@login_required
def request_return(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        reason = request.POST.get('reason')
        image = request.FILES.get('image')
        ReturnRequest.objects.create(order=order, customer=request.user, amount=order.total, image=image, status='pending')
        messages.success(request, "Return request submitted.")
        return redirect('order_list')

from django.views.decorators.http import require_POST
from .models import ReturnRequest
from django.core.files.storage import FileSystemStorage

@require_POST
@login_required
def create_return_request(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    reason = request.POST.get('reason')
    image = request.FILES.get('image')

    if not reason or not image:
        messages.error(request, "Reason and image are required.")
        return redirect('order_list')

    # Save image
    fs = FileSystemStorage()
    filename = fs.save(image.name, image)
    uploaded_image_url = fs.url(filename)

    ReturnRequest.objects.create(
        order=order,
        customer=request.user,
        amount=order.total,
        status='pending',
        created_at=timezone.now(),
        # optional: if you have image field
         image=uploaded_image_url
    )

    messages.success(request, "Return request submitted.")
    return redirect('order_list')

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import ReturnRequest
from django.contrib.auth.decorators import login_required

@login_required
def mark_return_collected(request, return_id):
    if request.method == 'POST':
        ret = get_object_or_404(ReturnRequest, id=return_id)

        # Check: Only assigned delivery boy can mark as collected
        if ret.assigned_to and ret.assigned_to.user == request.user:
            ret.status = 'collected'  # use 'collected' as the status
            ret.collected_at = timezone.now()
            ret.save()
            messages.success(request, f"Return #{ret.id} marked as collected.")
        else:
            messages.error(request, "You are not authorized to mark this return.")
    
    return redirect('deliveryboy_home')

























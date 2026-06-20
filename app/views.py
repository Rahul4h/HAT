#from email import message
from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout

from .forms import CommentForm,ShippingAddressForm,ProductForm,BlogForm,BlogImageForm
from .models import Contact,Blogs,Product,Profile,CartItem,Comment,ShippingAddress,Order,OrderItem,ChatMessage,DeliveryBoy,DeliveryOrder,ReturnRequest,Recommendation,BlogImage
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
from django.db import transaction
from django.db.models import Q,F, ExpressionWrapper, FloatField, Max, Value, Case, When
from django.forms import modelform_factory,inlineformset_factory
from django.utils import timezone

import traceback

from app.utils.email import send_email



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
        discount_percentage=Case(
            When(
                original_price__gt=0,
                then=ExpressionWrapper(
                    (F('original_price') - F('sale_price')) * 100 / F('original_price'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        )
    ).order_by('-id')[:30]

    delivery_products = Product.objects.filter(uploaded_by__isnull=False).annotate(
        discount_percentage=Case(
            When(
                original_price__gt=0,
                then=ExpressionWrapper(
                    (F('original_price') - F('sale_price')) * 100 / F('original_price'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
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
        'delivery_products': delivery_products,
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
from app.utils.email import send_email
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
          send_email(
             subject=subject,
             html_content=message,
             to_email=email
            )
          messages.success(request, "Please check your email to activate your account.")

        except Exception as e:
          print("EMAIL ERROR:", str(e))
          print(traceback.format_exc())
          messages.error(request, "Email sending failed. Try again later.")

          user.delete()
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


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    comments = Comment.objects.filter(product=product, parent=None).order_by('-created_at')  # Only parent comments

    can_comment = True  # You can modify this to check if user purchased the product
    
    related_blog = product.blogs.first()

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
        'available_quantity': _available_quantity(product),
        'post':related_blog,
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


def _available_quantity(product):
    quantities = [product.stock]
    if product.piece is not None and product.piece > 0:
        quantities.append(product.piece)
    return min(quantities)


def _reserve_product_quantity(product, quantity):
    available_quantity = _available_quantity(product)
    if available_quantity < quantity:
        return False, available_quantity

    product.stock = max(product.stock, 0)
    if product.piece is not None and product.piece > 0:
        product.piece = max(product.piece - quantity, 0)
    product.save(update_fields=['stock', 'piece'])
    return True, available_quantity


def _restore_product_quantity(product, quantity):
    product.stock += 0
    product.piece += quantity
    product.save(update_fields=['stock', 'piece'])


def _send_mail_safely(*args, **kwargs):
    kwargs.setdefault('fail_silently', True)
    try:
        send_mail(*args, **kwargs)
    except Exception:
        pass


def _create_delivery_order(order, product, shipping):
    assigned_delivery_boy = product.uploaded_by
    delivery_status = 'assigned' if assigned_delivery_boy else 'pending'

    if assigned_delivery_boy:
        order.delivery_status = 'assigned'
        order.save(update_fields=['delivery_status'])

    delivery_order, _ = DeliveryOrder.objects.get_or_create(
        order=order,
        defaults={
            'user': order.user,
            'assigned_to': assigned_delivery_boy,
            'status': delivery_status,
            'address': shipping.address,
            'total': float(order.total),
            'payment_method': order.payment_method,
        },
    )
    return delivery_order

@login_required
def checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    available_quantity = _available_quantity(product)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(quantity, 1)
    delivery_fee = 30
    subtotal = product.sale_price * quantity
    total = subtotal + delivery_fee

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        payment_method = request.POST.get('payment_method')

        if form.is_valid() and payment_method in ['stripe', 'cod']:
            if available_quantity < quantity:
                messages.error(request, f"Sorry, only {available_quantity} item(s) left in stock.")
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
            with transaction.atomic():
                product = Product.objects.select_for_update().get(id=product.id)
                reserved, available_quantity = _reserve_product_quantity(product, quantity)
                if not reserved:
                    messages.error(request, f"Sorry, only {available_quantity} item(s) left in stock.")
                    return redirect('checkout', product_id=product.id)

                order = Order.objects.create(
                    user=request.user,
                    shipping_address=shipping,
                    address=shipping.address,
                    payment_method='cod',
                    total=total
                )
                OrderItem.objects.create(order=order, product=product, quantity=quantity)
                _create_delivery_order(order, product, shipping)
            
            html_content = render_to_string(
                 "order_email.html",
                  {
                  "order": order,
                  "product": product,
                  "quantity": quantity,
                  "total": total,
                  }
               )
            try:
             send_email(
             subject=f"Order Confirmation #{order.id}",
             html_content=html_content,
             to_email=request.user.email,
            )
            except Exception as e:
             print("ORDER EMAIL ERROR:", str(e))

            return render(request, 'order_confirmation.html', {
                'product': product,
                'quantity': quantity,
                'total': total,
                'payment_method': 'cod',
                'shipping': shipping,
                'message': "✅ Your order has been placed with Cash on Delivery!",
                'order_id': order.id,
                'order': order,
            })
        else:
         messages.error(request, "Please correct the checkout form and try again.")

    else:
        form = ShippingAddressForm()

    context = {
        'product': product,
        'quantity': quantity,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'form': form,
        'available_quantity': available_quantity,
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
    available_quantity = _available_quantity(product)
    if available_quantity < quantity:
        messages.error(request, f"Sorry, the product is out of stock.")
        return redirect('checkout', product_id=product.id)

    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product.id)
        reserved, available_quantity = _reserve_product_quantity(product, quantity)
        if not reserved:
            messages.error(request, f"Sorry, only {available_quantity} item(s) left in stock.")
            return redirect('checkout', product_id=product.id)

        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping,
            address=shipping.address,
            payment_method='stripe',
            total=total
        )
        OrderItem.objects.create(order=order, product=product, quantity=quantity)
        _create_delivery_order(order, product, shipping)

    _send_mail_safely(
        subject="Your Stripe Order Confirmation",
        message=f"Thanks for paying via Stripe!\n\nOrder #{order.id}\nProduct: {product.title}\nQuantity: {quantity}\nTotal: ৳{total}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.user.email],
    )

    return render(request, 'order_confirmation.html', {
        'product': product,
        'quantity': quantity,
        'total': total,
        'payment_method': 'stripe',
        'shipping': shipping,
        'message': "✅ Your payment was successful via Stripe!",
        'order_id': order.id,
        'order': order,
    })

@login_required
def stripe_cancel(request):
    return render(request, 'cancel.html')




def initiate_sslcommerz_payment(request):
    if request.method == 'POST':
        if not settings.SSLCOMMERZ_STORE_ID or not settings.SSLCOMMERZ_STORE_PASSWORD:
            return JsonResponse({'error': 'SSLCommerz credentials are not configured.'}, status=503)

        amount = request.POST.get('amount')
        product_id = request.POST.get('product_id')

        if not amount or not product_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        data = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
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
            response = requests.post(settings.SSLCOMMERZ_API_URL, data=data, timeout=20)
            response_data = response.json()

            if 'GatewayPageURL' in response_data:
                return JsonResponse({'GatewayPageURL': response_data['GatewayPageURL']})
            else:
                return JsonResponse({'error': 'SSLCommerz response invalid', 'details': response_data}, status=500)

        except Exception as e:
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
        _restore_product_quantity(product, item.quantity)
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



@login_required
def update_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )


    OrderItemFormSet = inlineformset_factory(
        Order,
        OrderItem,
        fields=('quantity',),
        extra=0
    )


    ShippingForm = modelform_factory(
        ShippingAddress,
        fields=('address', 'phone')
    )


    shipping_instance = order.shipping_address



    if request.method == 'POST':

        formset = OrderItemFormSet(
            request.POST,
            instance=order
        )

        shipping_form = ShippingForm(
            request.POST,
            instance=shipping_instance
        )


        payment_method = request.POST.get('payment_method')



        if (
            formset.is_valid()
            and shipping_form.is_valid()
            and payment_method in ['stripe','cod']
        ):



            # ============================
            # Store old quantities
            # ============================

            old_quantities = {}

            for item in order.items.all():

                old_quantities[item.id] = item.quantity



            # save new quantities temporarily

            updated_items = formset.save(commit=False)



            # ============================
            # Check stock + update piece
            # ============================

            for item in updated_items:


                product = item.product


                old_qty = old_quantities.get(
                    item.id,
                    0
                )


                new_qty = item.quantity



                difference = new_qty - old_qty



                # quantity increased
                if difference > 0:


                    if product.piece < difference:

                        messages.error(
                            request,
                            f"{product.title} এর পর্যাপ্ত stock নেই"
                        )

                        return redirect(
                            'order_list'
                        )


                    product.piece -= difference



                # quantity decreased
                elif difference < 0:


                    product.piece += abs(
                        difference
                    )



                product.save()

                item.save()



            # ============================
            # Save shipping address
            # ============================


            shipping_address = shipping_form.save(
                commit=False
            )


            shipping_address.user = request.user

            shipping_address.save()



            order.shipping_address = shipping_address

            order.address = shipping_address.address

            order.payment_method = payment_method



            # ============================
            # Recalculate total
            # ============================


            total = 0

            delivery_fee = 30


            for item in order.items.all():

                total += (
                    item.product.sale_price
                    *
                    item.quantity
                )


            total += delivery_fee


            order.total = total


            order.save()



            # ============================
            # Stripe
            # ============================


            if payment_method == 'stripe':


                request.session[
                    'update_order_id'
                ] = order.id



                session = stripe.checkout.Session.create(

                    payment_method_types=[
                        'card'
                    ],


                    line_items=[

                        {

                        'price_data': {

                            'currency':'bdt',

                            'unit_amount':int(
                                total * 100
                            ),


                            'product_data':{

                                'name':
                                f"Order #{order.id}"

                            },

                        },


                        'quantity':1,

                        }

                    ],


                    mode='payment',


                    success_url=request.build_absolute_uri(
                        '/order/update/success/'
                    ),


                    cancel_url=request.build_absolute_uri(
                        '/order/update/cancel/'
                    ),

                )


                return JsonResponse(
                    {
                    'session_url':session.url
                    }
                )



            # ============================
            # COD
            # ============================


            messages.success(
                request,
                "Order updated successfully with Cash on Delivery."
            )


            return redirect(
                'order_list'
            )



        else:

            messages.error(
                request,
                "Please correct the errors below."
            )



    else:


        formset = OrderItemFormSet(
            instance=order
        )


        shipping_form = ShippingForm(
            instance=shipping_instance
        )



    return render(
        request,
        'update_order.html',
        {
            'order':order,
            'formset':formset,
            'shipping_form':shipping_form,
        }
    )

@login_required
def update_order_success(request):
    order_id = request.session.get('update_order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.payment_method = 'stripe'
    order.save()

    _send_mail_safely(
        subject="Your Updated Stripe Order Confirmation",
        message=f"Thanks! Order #{order.id} updated and paid successfully.\nTotal: ৳{order.total}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.user.email],
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

    my_products = Product.objects.filter(uploaded_by=deliveryboy).order_by('-id')[:10]
    my_blogs = Blogs.objects.filter(authname=request.user.username).order_by('-timeStamp')[:10]

    context = {
        'deliveryboy': deliveryboy,
        'pending_deliveries': pending_deliveries,
        'pending_returns': pending_returns,
        'my_deliveries': my_deliveries,
        'my_returns': my_returns,
        'my_products': my_products,
        'my_blogs': my_blogs,
    }

    return render(request, 'deliveryboy_home.html', context)


@login_required
def deliveryboy_add_product(request):
    if not hasattr(request.user, 'deliveryboy'):
        return redirect('deliveryboy_login')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.uploaded_by = request.user.deliveryboy
            if not product.piece:
                product.piece = product.stock
            try:
                product.save()
            except Exception as exc:
                messages.error(request, f"Product upload failed: {exc}")
                return render(request, 'deliveryboy_add_product.html', {'form': form})
            messages.success(request, "Product added successfully.")
            return redirect('deliveryboy_home')
    else:
        form = ProductForm()

    return render(request, 'deliveryboy_add_product.html', {'form': form})

@login_required
def deliveryboy_delete_product(request,id):

    if not hasattr(request.user,'deliveryboy'):
        return redirect('deliveryboy_login')


    product = get_object_or_404(
        Product,
        id=id,
        uploaded_by=request.user.deliveryboy
    )


    product.delete()

    messages.success(
        request,
        "Product deleted successfully"
    )

    return redirect('deliveryboy_home')

@login_required
def deliveryboy_update_product(request,id):

    if not hasattr(request.user,'deliveryboy'):
        return redirect('deliveryboy_login')


    product = get_object_or_404(
        Product,
        id=id,
        uploaded_by=request.user.deliveryboy
    )


    if request.method=="POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Product updated successfully"
            )

            return redirect('deliveryboy_home')


    else:

        form = ProductForm(instance=product)



    return redirect('deliveryboy_home')

@login_required
def deliveryboy_add_blog(request):

    if not hasattr(request.user, 'deliveryboy'):
        return redirect('deliveryboy_login')


    products = Product.objects.filter(
        uploaded_by=request.user.deliveryboy
    )


    if request.method == 'POST':

        form = BlogForm(request.POST, request.FILES)

        form.fields['product'].queryset = products


        if form.is_valid():

            # maximum 10 images check
            images = request.FILES.getlist('images')

            if len(images) > 10:
                messages.error(
                    request,
                    "Maximum 10 images are allowed."
                )
                return render(
                    request,
                    'deliveryboy_add_blog.html',
                    {'form': form}
                )


            blog = form.save(commit=False)
            blog.authname = request.user.username

            try:
              with transaction.atomic():
                blog.save()


                # save multiple images
                for img in images:
                    BlogImage.objects.create(
                        blog=blog,
                        image=img
                    )


            except Exception as exc:
                messages.error(
                    request,
                    f"Blog upload failed: {exc}"
                )

                return render(
                    request,
                    'deliveryboy_add_blog.html',
                    {'form': form}
                )


            messages.success(
                request,
                "Blog post added successfully."
            )

            return redirect('handleBlog')


    else:

        form = BlogForm()

        form.fields['product'].queryset = products



    return render(
        request,
        'deliveryboy_add_blog.html',
        {'form': form}
    )

@login_required
def deliveryboy_delete_blog(request,id):

    if not hasattr(request.user,'deliveryboy'):
        return redirect('deliveryboy_login')


    blog = get_object_or_404(
        Blogs,
        id=id,
        authname=request.user.username
    )


    blog.delete()


    messages.success(
        request,
        "Blog deleted successfully"
    )


    return redirect('handleBlog')

@login_required
def deliveryboy_update_blog(request,id):

    if not hasattr(request.user,'deliveryboy'):
        return redirect('deliveryboy_login')


    blog = get_object_or_404(
        Blogs,
        id=id,
        authname=request.user.username
    )


    products = Product.objects.filter(
        uploaded_by=request.user.deliveryboy
    )


    if request.method=="POST":

        form = BlogForm(
            request.POST,
            request.FILES,
            instance=blog
        )

        form.fields['product'].queryset = products


        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Blog updated successfully"
            )

            return redirect('handleBlog')


    else:

        form = BlogForm(instance=blog)
        form.fields['product'].queryset = products



    return redirect('deliveryboy_home')




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
    if not hasattr(request.user, 'deliveryboy'):
        return redirect('deliveryboy_login')

    if request.method == 'POST':
        return_id = request.POST.get('return_id')

        ret = get_object_or_404(
            ReturnRequest,
            id=return_id,
            status='pending',
            assigned_to__isnull=True
        )

        ret.assigned_to = request.user.deliveryboy
        ret.status = 'assigned'
        ret.save()

        messages.success(
            request,
            f'Return request #{ret.id} assigned successfully.'
        )

    return redirect('deliveryboy_home')




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
@require_POST
@login_required
def create_return_request(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    reason = request.POST.get('reason')
    image = request.FILES.get('image')

    if not reason or not image:
        messages.error(request, "Reason and image are required.")
        return redirect('order_list')

    ReturnRequest.objects.create(
        order=order,
        customer=request.user,
        amount=order.total,
        status='pending',
        created_at=timezone.now(),
        image=image,
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

























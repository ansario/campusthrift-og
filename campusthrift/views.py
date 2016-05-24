from django.shortcuts import render, redirect, HttpResponse

from braintree import WebhookNotification
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from users.models import UserProfile
import braintree
from shop.models import Item
from checkout.models import Order, OrderItem
from forms import UserForm, UserProfileForm, UserLoginForm, UserEditForm
import random, string


from django.contrib.auth import authenticate, login

def home(request):

    return render(request, 'campusthrift/home.html')

def order_view(request, order_number):

    order = Order.objects.get(primary_key=order_number)
    order_items = OrderItem.objects.all().filter(order=order)
    return render(request, 'campusthrift/order_view.html', {'order': order, 'order_items': order_items})

def profile(request):

    if not request.user:
                return redirect('login')
    else:
        user = User.objects.get(username=request.user)
        current_sales = Item.objects.all().filter(user=request.user, sold=False)
        orders = Order.objects.all().filter(buyer=user)

        pending_sold_items = OrderItem.objects.all().filter(seller=user, seller_confirmed=False)
        pending_purchased_items = OrderItem.objects.all().filter(order__buyer=user, buyer_confirmed=False)


        # need_to_ship = OrderItem.objects.all().filter(user=request.user, sold=True, buyer_confirmed=False)
        # waiting_for_seller =
        profile = request.user.user
        return render(request, 'campusthrift/profile.html',
                      {'user': user, 'profile': profile, 'current_sales':current_sales,
                       'orders': orders, 'pending_sold_items': pending_sold_items, 'pending_purchased_items': pending_purchased_items})



def profile_edit(request):

        if request.method == "POST":
            user_form = UserEditForm(request.POST, request.FILES, instance=request.user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.user)

            if user_form.is_valid():
                user_form.save()
            if profile_form.is_valid():
                profile_form.save()

            return redirect('profile')
        else:
            if not request.user:
                return redirect('login')
            else:
                user_form = UserEditForm(instance=request.user)
                profile_form = UserProfileForm(instance=request.user.user)
                return render(request, 'campusthrift/profile_edit.html',
                              {'user_form': user_form, 'profile_form': profile_form})

def user_login(request):
    if request.method == "POST":

        form = UserLoginForm(request.POST, request.FILES)


        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = ""

            try:
                user = User.objects.get(email=email)
            except:
                user = None

            if user is not None:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth = user.check_password(password)
                if auth:
                    #Check if authenticated user is active.
                    if user.is_active:
                        authenticate(username=user.username, password=password)
                        login(request, user)
                        return redirect('home')
                    #If user is authenticated but user is not active.
                    else:
                        return render(request, 'campusthrift/login.html', {'form': form, 'error': "Your account is not activated! Check your"
                                                                                    " email for the activation link!"})
                #User is not authorized.
                else:
                    return render(request, 'campusthrift/login.html', {'form': form, 'error': "Invalid password."})
            #User does not exist with that email.
            else:
                return render(request, 'campusthrift/login.html', {'form': form, 'error': "We could not find an account with that email!"})


    else:
        # form = UserRegistrationForm()
        form = UserLoginForm()

        return render(request, 'campusthrift/login.html', {'form': form})

    # return render(request, 'campusthrift/login.html')


def register(request):

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(request.POST, request.FILES)
        profile_form = UserProfileForm(request.POST, request.FILES)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.is_active = False
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.activation_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            print request.FILES
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

            result = braintree.MerchantAccount.create({
				'individual' : {
					'first_name' : user.first_name,
					'last_name' : user.last_name,
					'email': user.email,
					'date_of_birth': profile.date_of_birth,
                    'address': {
						'street_address':"23 Cameron St.",
						'locality':profile.city,
						'region':profile.state,
						'postal_code':profile.zip
					}
				},
				'funding': {
					'descriptor': "Campusthrift",
					'destination': braintree.MerchantAccount.FundingDestination.Email,
					'email': user.email
				},
				"tos_accepted":True,
				"master_merchant_account_id":"CAMPUSTHRIFT"
			})

            customer_result = braintree.Customer.create({
                "id": profile.primary_key,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,

            })

            profile.braintree_customer_id = customer_result.customer.id
            profile.braintree_merchant_id = result.merchant_account.id
            profile.save()

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request,
            'campusthrift/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered} )

def seller_confirm(request, id):
    order_number = id[:10]
    order_item_id = id[10:]
    print order_number
    print order_item_id
    order_item = OrderItem.objects.get(order_id=order_number, pk=order_item_id)
    order_item.seller_confirmed = True
    order_item.save()
    return redirect('profile')

def buyer_confirm(request, id):
    order_number = id[:10]
    order_item_id = id[10:]
    print order_number
    print order_item_id
    order_item = OrderItem.objects.get(order_id=order_number, pk=order_item_id)
    order_item.buyer_confirmed = True
    order_item.save()



    result = braintree.Transaction.release_from_escrow(order_item.braintree_id_transaction)
    # print result.transaction.escrow_status
    # testing_gateway = braintree.TestingGateway(braintree.Configuration.gateway())
    # testing_gateway.settle_transaction(result.transaction.id)
    # testing_gateway.settlement_confirm_transaction(order_item.braintree_id_transaction)

    # updated_transaction = braintree.Transaction.find(order_item.braintree_id_transaction)
    # print updated_transaction.escrow_status
    return redirect('profile')

@csrf_exempt
def webhook(request):
    if 'bt_challenge' in request.GET:
        challenge = request.GET['bt_challenge']
        return HttpResponse(WebhookNotification.verify(challenge))
    elif 'bt_signature' in request.POST and 'bt_payload' in request.POST:
        bt_signature = str(request.POST['bt_signature'])
        bt_payload = str(request.POST['bt_payload'])
        notification = WebhookNotification.parse(bt_signature, bt_payload)
        return handle_webhook_notficiation(notification)
    else:
        return HttpResponse("I don't understand you")

		# if(notification.kind == braintree.WebhookNotification.
         #               Kind.SubMerchantAccountApproved):
		# 	print notification.merchant_account.status
		# 	print notification.merchant_account.id
		# elif(notification.kind == braintree.WebhookNotification.
         #               Kind.SubMerchantAccountDeclined):
		# 	print notification.message
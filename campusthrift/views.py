from django.shortcuts import render, redirect, HttpResponse

from braintree import WebhookNotification
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from users.models import UserProfile
import braintree
import stripe
import time, datetime
import logging
log = logging.getLogger(__name__)
from shop.models import Item
from checkout.models import Order, OrderItem
from forms import UserForm, UserProfileForm, UserLoginForm, UserEditForm
import random, string
import datetime
from django.http import Http404
import os
from campusthrift.settings import PROJECT_ROOT, HOSTED_URL, SG_KEY, STRIPE_API_KEY
import sendgrid
import re
import base64
from django.contrib.auth import logout
sg = sendgrid.SendGridClient(SG_KEY)
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

stripe.api_key = STRIPE_API_KEY




from django.contrib.auth import authenticate, login

def home(request):

    items= list( Item.objects.all() )
    random.shuffle( items )
    item_list = items[:8]


    return render(request, 'campusthrift/home.html', {'items': item_list})

def about(request):
    return render(request, 'campusthrift/about.html')

def password_reset(request):

    errors = []

    if request.method == "POST":


        if 'email' in request.POST:

            if User.objects.filter(email=request.POST['email']).exists():

                user = User.objects.get(email=request.POST['email'])

                password_reset_key = base64.urlsafe_b64encode(str(user.email))

                base_activation_email_template = open(os.path.join(PROJECT_ROOT, 'emails/password_reset_email.html')).read()
                personal_reset_link = HOSTED_URL + "/password_reset/" + password_reset_key
                personal_reset_email_template = base_activation_email_template.replace("@@@RESET_URL@@@", personal_reset_link)

                message = sendgrid.Mail(to=user.email, subject='CampusThrift Password Reset', html=personal_reset_email_template, text='Body', from_email='noreply@campusthrift.com')
                sg.send(message)
                return redirect('home')


            else:
                errors.append("That email was not found in our database.")
        else:
            errors.append("There was a problem with your request, please try again!")

        if not errors:
                return redirect('home')
        else:
                return render(request, 'campusthrift/reset.html', {"errors": errors})

    else:

        return render(request, 'campusthrift/reset.html')

def password_reset_confirm(request, uidb64):

    errors = []

    if uidb64:

        if request.method == "GET":

            return render(request, 'campusthrift/reset_confirm.html')

        if request.method == "POST":

            user_email = base64.urlsafe_b64decode(str(uidb64))

            if User.objects.filter(email=user_email).exists():

                user = User.objects.get(email=user_email)

                user.set_password(request.POST['password'])
                user.save()
                return redirect('home')

            else:

                errors.append("There was a problem resetting your password, please try again!")
                return render(request, 'campusthrift/reset_confirm.html', {"errors": errors })




    else:
        return redirect('home')



@login_required(login_url='/login')
def order_view(request, order_number):

    order = Order.objects.get(primary_key=order_number)
    order_items = OrderItem.objects.all().filter(order=order)
    return render(request, 'campusthrift/order_view.html', {'order': order, 'order_items': order_items})

@login_required(login_url='/login')
def profile(request):

    if not request.user:
                return redirect('login')
    else:
        user = User.objects.get(username=request.user)
        current_sales = Item.objects.all().filter(user=request.user, sold=False)
        orders = Order.objects.all().filter(buyer=user)

        pending_sold_items = OrderItem.objects.all().filter(seller=user, seller_confirmed=False, order__canceled=False)
        pending_purchased_items = OrderItem.objects.all().filter(order__buyer=user, buyer_confirmed=False,  order__canceled=False)


        # need_to_ship = OrderItem.objects.all().filter(user=request.user, sold=True, buyer_confirmed=False)
        # waiting_for_seller =
        profile = request.user.user

        stripe_customer = stripe.Customer.retrieve(profile.stripe_customer_id)
        payment_info = stripe_customer.sources.retrieve(stripe_customer.default_source)
        return render(request, 'campusthrift/profile.html',
                      {'user': user, 'profile': profile, 'current_sales':current_sales,
                       'orders': orders, 'pending_sold_items': pending_sold_items, 'pending_purchased_items': pending_purchased_items, 'payment_information': payment_info})


@login_required(login_url='/login')
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

@login_required(login_url='/login')
def payment_edit(request):
    errors = []

    if request.method == "POST":

        print request.POST

        if 'stripeTokenCustomer' in request.POST and 'stripeTokenSeller' in request.POST and 'ssn' in request.POST:



                stripe_customer_object = stripe.Customer.retrieve(request.user.user.stripe_customer_id)
                stripe_account_object = stripe.Account.retrieve(request.user.user.stripe_account_id)

                try:

                    customer_card = stripe_customer_object.sources.create(source=request.POST['stripeTokenCustomer'])
                    account_card = stripe_account_object.external_accounts.create(external_account=request.POST['stripeTokenSeller'])
                    account_card.default_for_currency = True
                    account_card.save()
                    # print account_card
                    stripe_customer_object.default_source = customer_card.id

                except stripe.InvalidRequestError, e:
                    print e


                    errors.append("Bank card entered is not a valid debit card! We require debit cards to pay you for sales.")


                birth_array = str(request.user.user.date_of_birth).split('-')



                stripe_account_object.legal_entity.dob.day = birth_array[2]
                stripe_account_object.legal_entity.dob.month = birth_array[1]
                stripe_account_object.legal_entity.dob.year = birth_array[0]
                stripe_account_object.legal_entity.first_name = request.user.first_name
                stripe_account_object.legal_entity.last_name = request.user.last_name
                stripe_account_object.legal_entity.type = "individual"
                stripe_account_object.tos_acceptance.date = int(time.time())
                stripe_account_object.tos_acceptance.ip = '8.8.8.8'
                stripe_account_object.legal_entity.address.line1 = request.POST['address']
                stripe_account_object.legal_entity.address.city = request.POST['city']
                stripe_account_object.legal_entity.address.state = request.POST['state']
                stripe_account_object.legal_entity.address.postal_code = request.POST['zip']
                stripe_account_object.legal_entity.ssn_last_4 =  request.POST['ssn']

                if not errors:
                    try:
                        stripe_customer_object.save()
                        stripe_account_object.save()
                        return redirect('profile')
                    except Exception, e:
                        print e
                        errors.append("Please verify your financial details")
                        return render(request, 'campusthrift/payment_edit.html', {'errors': errors})
                else:
                    return render(request, 'campusthrift/payment_edit.html', {'errors': errors})
        else:
            errors.append("There was an error with your payment information!")
            return render(request, 'campusthrift/payment_edit.html', {'errors': errors})


    else:
        return render(request, 'campusthrift/payment_edit.html')


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
                    if user.user.graduated:
                        return render(request, 'campusthrift/login.html', {'form': form, 'error': "Congratulations on graduating! CampusThrift is only available to current students."})

                    elif user.is_active:
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
    errors = []

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.



        user = User()
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']

        tld = ""

        try:
            p = re.compile("([^.]+$)")
            tld = p.search(request.POST['email']).group(1)
        except:
            errors.append("You must sign up with a valid .edu email address.")

        if tld == "edu":
            user.email = request.POST['email']
        else:
            errors.append("You must sign up with a valid .edu email address.")


        if User.objects.filter(username=request.POST['username']).exists():
            errors.append("The username you chose has already been taken.")
        else:
            user.username = request.POST['username']

        user.set_password(request.POST['password'])
        user.is_active = False


        profile = UserProfile()


        profile.activation_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))
        profile.date_of_birth = request.POST['date_of_birth']
        profile.school = request.POST['school']

        now = datetime.datetime.now()
        graduation_year = int(request.POST['graduation_year'])
        max_graduation_year = int(now.year + 10)

        if graduation_year  > max_graduation_year:
            errors.append("Your graduation year is too far ahead in the future!")
        elif graduation_year < now.year - 1:
            errors.append("It looks like you already graduated! CampusThrift is open to current students only.")
        else:
            profile.graduation_year = graduation_year

        profile.picture = request.FILES['picture']
        profile.address = request.POST['address']
        profile.city = request.POST['city']
        profile.state = request.POST['state']
        profile.zip = request.POST['zip']

        if not errors and 'stripeTokenCustomer' in request.POST and 'stripeTokenSeller' in request.POST and 'ssn' in request.POST:


            stripe_customer_object = stripe.Customer.create(
                description = user.first_name + " " + user.last_name + " customer account",

            )

            stripe_account_object = stripe.Account.create (
                managed=True,
                country="US",
                email = user.email,
                default_currency="usd"
            )




            try:

                customer_card = stripe_customer_object.sources.create(source=request.POST['stripeTokenCustomer'])
                account_card = stripe_account_object.external_accounts.create(external_account=request.POST['stripeTokenSeller'])

            except stripe.InvalidRequestError:


                errors.append("Bank card entered is not a valid debit card! We require debit cards to pay you for sales.")


            birth_array = profile.date_of_birth.split('-')



            stripe_account_object.legal_entity.dob.day = birth_array[2]
            stripe_account_object.legal_entity.dob.month = birth_array[1]
            stripe_account_object.legal_entity.dob.year = birth_array[0]
            stripe_account_object.legal_entity.first_name = user.first_name
            stripe_account_object.legal_entity.last_name = user.last_name
            stripe_account_object.legal_entity.type = "individual"
            stripe_account_object.tos_acceptance.date = int(time.time())
            stripe_account_object.tos_acceptance.ip = '8.8.8.8'
            stripe_account_object.legal_entity.address.line1 = profile.address
            stripe_account_object.legal_entity.address.city = profile.city
            stripe_account_object.legal_entity.address.state = profile.state
            stripe_account_object.legal_entity.address.postal_code = profile.zip
            stripe_account_object.legal_entity.ssn_last_4 =  request.POST['ssn']




            # stripe_account.external_account = request.POST['stripeToken']



            profile.stripe_customer_id = stripe_customer_object.id
            profile.stripe_account_id = stripe_account_object.id

            if not errors:
                try:
                    stripe_customer_object.save()
                    stripe_account_object.save()
                except:
                    errors.append("Please verify your financial details")
                    return render(request,
                    'campusthrift/register.html',
                    {'registered': registered, 'errors': errors} )

        else:
            errors.append("There was an error with your payment information!")
            return render(request,
                    'campusthrift/register.html',
                    {'registered': registered, 'errors': errors} )

        if not errors:
            try:
                user.save()
                profile.user = user
                profile.save()
            except Exception, e:
                errors.append("There was a problem creating your account, please try again!")
                print str(e)
                return render(request,
                'campusthrift/register.html',
                {'registered': registered, 'errors': errors} )
        else:
            return render(request,
            'campusthrift/register.html',
            {'registered': registered, 'errors': errors} )



        base_activation_email_template = open(os.path.join(PROJECT_ROOT, 'emails/activation_email.html')).read()
        personal_activation_link = HOSTED_URL + "/activate/" + profile.activation_key
        personal_activation_email_template = base_activation_email_template.replace("@@@ACTIVATION_URL@@@", personal_activation_link)



        message = sendgrid.Mail(to=user.email, subject='CampusThrift Activation', html=personal_activation_email_template, text='Body', from_email='noreply@campusthrift.com')
        sg.send(message)


        return redirect('user_login')

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.



    # Render the template depending on the context.
    return render(request,
            'campusthrift/register.html',
            {'registered': registered} )

@login_required(login_url='/login')
def seller_confirm(request, id):
    order_number = id[:10]
    order_item_id = id[10:]

    order = Order.objects.get(primary_key=order_number)

    if order.in_progress == False:
        order.in_progress = True
        order.save()

    order_item = OrderItem.objects.get(order_id=order_number, pk=order_item_id)
    order_item.seller_confirmed = True
    order_item.save()


    order_items = OrderItem.objects.all().filter(order_id=order_number)

    incomplete = False
    for order_item_check in order_items:

        if not order_item_check.buyer_confirmed or not order_item_check.seller_confirmed:
            incomplete = True

    order.in_progress = incomplete

    order.save()


    return redirect('profile')

@login_required(login_url='/login')
def buyer_confirm(request, id):
    order_number = id[:10]
    order_item_id = id[10:]

    order = Order.objects.get(primary_key=order_number)

    if order.in_progress == False:
        order.in_progress = True
        order.save()


    order_item = OrderItem.objects.get(order_id=order_number, pk=order_item_id)
    order_item.buyer_confirmed = True
    order_item.seller_confirmed = True
    order_item.save()

    seller_stripe_account = stripe.Account.retrieve(order_item.seller.user.stripe_account_id)


    stripe.Transfer.create(
        amount = int((float(order_item.order_item_total_price) * 100)),
        currency = "usd",
        destination = seller_stripe_account,
        description = "Transfer for " + order_item.seller.email,
        application_fee = int(float(order_item.order_item_total_price) * 100 * .15)
    )

    order_items = OrderItem.objects.all().filter(order_id=order_number)

    incomplete = False
    for order_item_check in order_items:

        if not order_item_check.buyer_confirmed or not order_item_check.seller_confirmed:
            incomplete = True

    order.in_progress = incomplete
    if order.in_progress == False:
        order.complete = True

    order.save()

    return redirect('profile')

@login_required(login_url='/login')
def cancel_order(request, pk):

    if Order.objects.filter(pk=pk).exists():
        order = Order.objects.get(pk=pk)

        if order.buyer == request.user:

            order.canceled = True
            order.in_progress = False
            order.complete = False
            order.save()

            order_items = OrderItem.objects.all().filter(order=order)

            for item in order_items:
                item.item.sold = False
                re = stripe.Refund.create(
                    charge=item.stripe_charge_id
                )
                item.item.save()

    return redirect('profile')

def activate(request, activation_key):
    try:
        user_profile = UserProfile.objects.get(activation_key=activation_key)
        user = user_profile.user
        user.is_active = True
        user.save()


        return redirect('home')
    ###TODO
    except:
        pass


def user_store(request, user):

    try:
        user = User.objects.get(username=user)
        items = Item.objects.all().filter(user=user)

        return render(request, 'campusthrift/user_shop.html', {"user":user, "items":items})
    except:
        raise Http404("No MyModel matches the given query.")

def handler404(request):
    return render(request, 'campusthrift/404.html')

def logout_user(request):
    logout(request)
    return redirect('home')
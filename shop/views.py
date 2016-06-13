from django.shortcuts import render, HttpResponse, redirect
from django.forms import modelformset_factory, BaseFormSet
from django import forms
import stripe
from campusthrift.settings import STRIPE_API_KEY
from users.models import UserProfile
from campusthrift.forms import ItemForm, ImageForm
from models import Category, Subcategory, Item, ItemImage
import simplejson
from PIL import Image
from django.contrib.auth.decorators import login_required
stripe.api_key = STRIPE_API_KEY
from watson import search as watson
# Create your views here.
def shop(request):

    if 'q' in request.GET:

        items = watson.filter(Item, request.GET['q'])
        categories = Category.objects.all()

    else:
        items = Item.objects.all().filter(user__user__graduated=False, sold=False)
        categories = Category.objects.all()

    return render(request, 'shop/shop.html', {'items':items, 'categories':categories})

def shop_category(request, category):

    items = Item.objects.all().filter(sold=False,category=category, user__user__graduated=False)
    categories = Category.objects.all()
    return render(request, 'shop/shop.html', {'items':items, 'categories':categories})

def shop_subcategory(request, category, subcategory):

    category = category.replace("%20", ' ')
    subcategory = subcategory.replace("%20", ' ')

    items = Item.objects.all().filter(category=category,sold=False, sub_category=subcategory, user__user__graduated=False)
    categories = Category.objects.all()

    return render(request, 'shop/shop.html', {'items': items, 'categories': categories})


def cart_delete(request, pk):

    cart = request.session.get('cart', {})
    try:
        del cart[pk]
        request.session['cart'] = cart
        return redirect('view_cart')
    except:
        return redirect('view_cart')


def delete_item(request, pk):

    errors = []



    if Item.objects.filter(pk=pk).exists():
        if Item.objects.get(pk=pk).user == request.user:
            Item.objects.filter(pk=pk).delete()

    return redirect('profile')





@login_required(login_url='/login')
def new(request):

    errors = []

    if request.method == "POST":


        form = ItemForm(request.POST)

        saved_item = None

        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            item.category = request.POST['selectcategories']
            item.sub_category = request.POST['selectsubcategories']
            saved_item = item


        imageForm = ImageForm(request.POST, request.FILES)
        print imageForm
        if len(request.FILES) != 0 and saved_item:

            # raise forms.ValidationError(("At least one image is required for new listings."))

            for image in request.FILES:

                new_image = ItemImage()
                new_image.image = request.FILES[image]
                new_image.rotation = request.POST[str(image).replace("picture", "rotation")]
                new_image.item = saved_item
                new_image.save()

                im = Image.open(new_image.image)
                rotated_image = im.rotate(-1 * float(new_image.rotation))
                rotated_image.save(new_image.image.file.name, overwrite=True)


            if request.user.user.listed_first_item:

                result = stripe.Charge.create(
                       amount = int(50),
                       currency = "usd",
                       customer = request.user.user.stripe_customer_id,
                       description = "Listing fee for " + saved_item.title
                )
                saved_item.stripe_listing_fee_id = result.id
                saved_item.save()
            else:
                request.user.user.listed_first_item = True
                request.user.user.save()
                saved_item.stripe_listing_fee_id = "FIRSTTIME"
                saved_item.save()

            return redirect('shop')
            # print request.FILES[image]
        else:
            errors.append("You must upload at least one image!")

        if not saved_item:
            errors.append("Looks like your submission was incomplete!")
    else:
        form =ItemForm()
        imageForm = ImageForm()
    items = Category.objects.all()

    ImageFormSet = modelformset_factory(ItemImage, form=ImageForm, max_num=10, min_num=1, validate_min=True)

    formset = ImageFormSet(queryset=ItemImage.objects.none())

    return render(request, 'shop/new.html', {'form':form, 'categories': items, 'imageForm': imageForm, 'formset': formset, 'error':errors})


@login_required(login_url='/login')

def view_cart(request):

    cart = request.session.get('cart', {})
    item_list = []
    for id in cart:
        try:
            item = Item.objects.get(pk=id)
            item_list.append(item)
        except:
            pass


    return render(request, 'shop/cart.html', {'cart': item_list})
    # rest of the view



def view_item(request, pk):

    if request.method == "POST":

        item = request.POST['item']

        #Add one item to cart.
        cart = request.session.get('cart', {})
        cart[item] = 1
        request.session['cart'] = cart

        return redirect('view_item', pk)

    else:

        item = None


        try:
            item = Item.objects.get(pk=pk)

        except:
            pass

        if item:
            pictures = item.images.all()

            return render(request, 'shop/view.html', {'item':item, 'seller':item.user.user, 'pictures':pictures})



def getdetails(request):
    #country_name = request.POST['country_name']
    print(request.body)
    category_name = request.GET['cnt']
    print category_name

    # print(request.data)

    result_set = []
    all_subcategories = []
    answer = str(category_name[1:-1])
    selected_category = Category.objects.get(name=answer)

    all_subcategories = selected_category.subcategories.all()
    for subcategory in all_subcategories:

        result_set.append({'name': subcategory.name})

    return HttpResponse(simplejson.dumps(result_set), content_type='application/json')


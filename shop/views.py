from django.shortcuts import render, HttpResponse, redirect
from django.forms import modelformset_factory, BaseFormSet
from django import forms
from users.models import UserProfile
from campusthrift.forms import ItemForm, ImageForm
from models import Category, Subcategory, Item, ItemImage
import simplejson
from PIL import Image
# Create your views here.
def shop(request):


    return render(request, 'shop/shop.html')

def new(request):

    errors = []

    if request.method == "POST":


        form = ItemForm(request.POST)

        saved_item = None

        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            saved_item = item


        imageForm = ImageForm(request.POST, request.POST)
        print imageForm
        if len(request.FILES) != 0 and saved_item:

            # raise forms.ValidationError(("At least one image is required for new listings."))

            for image in request.FILES:

                new_image = ItemImage()
                new_image.image = request.FILES[image]
                new_image.rotation = request.POST[str(image).replace("image", "rotation")]
                new_image.item = saved_item
                new_image.save()

                im = Image.open(new_image.image)
                rotated_image = im.rotate(-1 * float(new_image.rotation))
                rotated_image.save(new_image.image.file.name, overwrite=True)

            redirect('shop')
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
    category_name = request.GET['cnt']


    result_set = []
    all_subcategories = []
    answer = str(category_name[1:-1])
    selected_category = Category.objects.get(name=answer)

    all_subcategories = selected_category.subcategory_set.all()
    for subcategory in all_subcategories:

        result_set.append({'name': subcategory.name})

    return HttpResponse(simplejson.dumps(result_set), content_type='application/json')


from django.forms import ModelForm
import django.forms as forms
from django.forms.widgets import TextInput
from django.contrib.auth.models import User
from users.models import UserProfile
from shop.models import Item, ItemImage




class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['picture', 'school', 'graduation_year', 'date_of_birth', 'address', 'city', 'state', 'zip']

class UserForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')

class UserEditForm(ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class UserLoginForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ('email', 'password')

class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ('title', 'description', 'price', 'shipping_price', 'shipping','meeting_place')
        # exclude = ('user', 'sold', 'stripe_listing_fee_id', 'category', 'sub_category')

class ImageForm(ModelForm):
    class Meta:
        model = ItemImage
        fields = ('image', 'rotation' )
        widgets = {'rotation': forms.HiddenInput(), 'class' : 'myfieldclass'}

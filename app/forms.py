from django import forms
from .models import Comment,ShippingAddress,Product,Blogs

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'parent']  # Include 'parent' to allow replies

        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Write your comment...'
            }),
            'parent': forms.HiddenInput(),  # Hidden input for replies
        }
        labels = {
            'content': '',
        }

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'phone']
        widgets = {
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your shipping address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'category', 'image', 'original_price', 'sale_price', 'stock', 'piece']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'original_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'piece': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def clean_original_price(self):
        original_price = self.cleaned_data['original_price']
        if original_price <= 0:
            raise forms.ValidationError("Original price must be greater than 0.")
        return original_price


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blogs
        fields = ['title', 'description', 'img', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'img': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

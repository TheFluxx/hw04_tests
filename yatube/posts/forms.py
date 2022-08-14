from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from .models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {
            'name': _('Creating post'),
        }
        help_texts = {
            'name': _('This is the form to crating a new post'),
        }

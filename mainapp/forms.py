from django import forms
from .utils import get_kv, LICENSES

class TagField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            kwargs['widget'] = forms.TextInput(
                attrs={'placeholder': 'shape=pyramidal, building=yes'})

        super(TagField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # Normalize string to a dict, representing the tags
        if not value:
            return {}

        tags = {}
        tag_list = value.split(', ')
        for tag in tag_list:
            try:
                k, v = get_kv(tag)
                tags[k] = v
            except ValueError:
                raise forms.ValidationError(f'Invalid tag: {tag}', code='invalid')

        return tags

class CategoriesField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            kwargs['widget'] = forms.TextInput(
                attrs={'placeholder': 'monuments, tall'})

        super(CategoriesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # Normalize string to a list of categories
        if not value:
            return []

        return value.split(', ')

class UploadForm(forms.Form):
    title = forms.CharField(
        label='Name', min_length=1, max_length=32, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Eiffel Tower'}))

    description = forms.CharField(
        label='Description', max_length=512,
        widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}), required=False)

    latitude = forms.FloatField(
        label='Latitude', min_value=-90, max_value=90, required=False, localize=False,
        widget=forms.NumberInput(attrs={'placeholder': '2.294481'}))

    longitude = forms.FloatField(
        label='Longitude', min_value=-180, max_value=180, required=False, localize=False,
        widget=forms.NumberInput(attrs={'placeholder': '48.858370'}))

    categories = CategoriesField(
        label='Categories', max_length=1024, required=False)
    
    tags = TagField(
        label='Tags', max_length=1024, required=False)

    license = forms.ChoiceField(
        label='License', required=True, choices=LICENSES.items(),
        widget=forms.RadioSelect)

    model_file = forms.FileField(
        label='Model File', required=True, allow_empty_file=False)

    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)

        # add class="form-control" to all fields
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

        # remove from license and model_file
        for field in ['license', 'model_file']:
            del self.fields[field].widget.attrs['class']

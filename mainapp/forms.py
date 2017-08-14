from django import forms
from .utils import get_kv, LICENSES

class TagField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            kwargs['widget'] = forms.TextInput(
                attrs= {
                    'placeholder': 'shape=pyramidal, building=yes',
                    'pattern': '^.*?(?==)((?!, ).)*(, .*?(?==)((?!, ).)*)*$',
                })

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
                raise forms.ValidationError('Invalid tag: {}'.format(tag), code='invalid')

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

class TranslationField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            kwargs['widget'] = forms.TextInput(
                attrs={
                    'value': '0.0 0.0 0.0',
                    'placeholder': '3 -4.5 1.03',
                    'pattern': '^(+|-)?[0-9]+(\.[0-9]+)? (+|-)?[0-9]+(\.[0-9]+)? (+|-)?[0-9]+(\.[0-9]+)?$'
                })

            super(TranslationField, self).__init__(*args, **kwargs)
    
    def to_python(self, value):
        # Normalize string to a list of 3 ints
        if not value:
            return [0, 0, 0] # default value

        numbers = list(map(float, value.split(' ')))

        if len(numbers) != 3:
            raise forms.ValidationError('Too many values', code='invalid')
        
        return numbers

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

    translation = TranslationField(
        label='Translation', max_length=100, required=False)

    rotation = forms.FloatField(
        label='Rotation', min_value=0, max_value=360, required=True, localize=True,
        widget=forms.NumberInput(attrs={'placeholder': '45.5', 'value': '0.0'}))

    scale = forms.FloatField(
        label='Scale', required=True, localize=True,
        widget=forms.NumberInput(attrs={'placeholder': '1.2', 'value': '1.0'}))

    license = forms.ChoiceField(
        label='License', required=False, choices=LICENSES.items(), initial=0,
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

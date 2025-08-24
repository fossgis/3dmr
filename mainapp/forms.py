from django import forms
from django.conf import settings
from .utils import get_kv, LICENSES_FORM, validate_glb_file

class TagField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            kwargs['widget'] = forms.TextInput(
                attrs = {
                    'placeholder': 'shape=pyramidal, building=yes',
                    'pattern': '^ *((((?!, )[^=])+=((?!, ).)+)(, ((?!, )[^=])+=((?!, ).)+)*)? *$',
                })

        super(TagField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # Normalize string to a dict, representing the tags
        if not value:
            return {}

        tags = {}
        tag_list = value.strip().split(', ')
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
                attrs = {
                    'placeholder': 'monuments, tall',
                    'pattern': '^ *(((?!, ).)+)(, ((?!, ).)+)* *$',
                })

        super(CategoriesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # Normalize string to a list of categories
        if not value:
            return []

        return value.strip().split(', ')

class OriginField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            kwargs['widget'] = forms.TextInput(
                attrs={
                    'value': '0.0 0.0 0.0',
                    'placeholder': '3 -4.5 1.03',
                    'pattern': r'^(\+|-)?[0-9]+((\.|,)[0-9]+)? (\+|-)?[0-9]+((\.|,)[0-9]+) (\+|-)?[0-9]+((\.|,)[0-9]+)$',
                    'aria-describedby': 'translation-help'
                })

            super(OriginField, self).__init__(*args, **kwargs)
    
    def to_python(self, value):
        # Normalize string to a list of 3 ints
        if not value:
            return [0, 0, 0] # default value

        numbers = list(map(lambda x: -float(x), value.replace(',', '.').split(' ')))

        if len(numbers) != 3:
            raise forms.ValidationError('Too many values', code='invalid')
        
        return numbers

class CompatibleFloatField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('widget'):
            if kwargs.get('attrs'):
                attrs = kwargs['attrs']
            else:
                attrs = {}
            attrs['pattern'] = r'^(\+|-)?[0-9]+((\.|,)[0-9]+)?$'

            kwargs['widget'] = forms.TextInput(attrs)

        kwargs = kwargs.copy()
        kwargs.pop('attrs')

        super(CompatibleFloatField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        # Normalize string to a dict, representing the tags
        if value == '' or value == None:
            return None

        try:
            number = float(value.replace(',', '.'))
        except ValueError:
            raise forms.ValidationError('Invalid number.', code='invalid')

        return number

class ModelField(forms.FileField):
    def validate(self, model):
        super().validate(model)

        if (model.size > settings.MAX_MODEL_SIZE):
            raise forms.ValidationError(
                'File size exceeds the maximum allowed size of {} MB.'.format(
                    settings.MAX_MODEL_SIZE / (1024 * 1024)
                ),
                code='file_too_large'
            )

        validate_glb_file(model)


# This function adds the 'form-control' class to all fields, with possible exceptions
def init_bootstrap_form(fields, exceptions=[]):
    # add class="form-control" to all fields
    for field in fields:
        fields[field].widget.attrs['class'] = 'form-control'

    # remove from exceptions
    for field in exceptions:
        del fields[field].widget.attrs['class']

class UploadFileForm(forms.Form):
    model_file = ModelField(
        label='Model File', required=True, allow_empty_file=False)

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        init_bootstrap_form(self.fields, ['model_file'])

class MetadataForm(forms.Form):
    title = forms.CharField(
        label='Name', min_length=1, max_length=32, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Eiffel Tower'}))

    description = forms.CharField(
        label='Description', max_length=512,
        widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}), required=False)

    latitude = CompatibleFloatField(
        label='Latitude', required=False,
        attrs={'placeholder': '2.294481'})

    longitude = CompatibleFloatField(
        label='Longitude', required=False,
        attrs={'placeholder': '48.858370'})

    categories = CategoriesField(
        label='Categories', max_length=1024, required=False)
    
    tags = TagField(
        label='Tags', max_length=1024, required=False)

    model_source = forms.ChoiceField(
        label='Where does the model come from?',
        choices=[
            ('self_created', 'I have created the model myself.'),
            ('other_source', 'I have taken the model from another source.')
        ],
        required=True, widget=forms.RadioSelect
    )

    source = forms.CharField(
        label='Source',
        max_length=255,
        required=False
    )

    license = forms.ChoiceField(
        label='License', required=True, choices=LICENSES_FORM.items(), initial=0,
        widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super(MetadataForm, self).__init__(*args, **kwargs)
        init_bootstrap_form(self.fields, ['model_source', 'license'])

    def clean_source(self):
        if self.cleaned_data.get('model_source') == 'other_source' and not self.cleaned_data['source']:
            raise forms.ValidationError('Please specify the other source.', code='required')
        return self.cleaned_data['source']

# This class represents a mix of the UploadFileForm and the MetadataForm
class UploadFileMetadataForm(MetadataForm):
    model_file = ModelField(
        label='Model File', required=True, allow_empty_file=False)

    def __init__(self, *args, **kwargs):
        super(UploadFileMetadataForm, self).__init__(*args, **kwargs)
        init_bootstrap_form(self.fields, ['model_source', 'license', 'model_file'])


class UserDescriptionForm(forms.Form):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'cols': '100', 'rows': '6'}),
        max_length=2048
    )
from django.utils.safestring import mark_safe

# Gets the key and value of an OSM tag from a string
# Note: any extra '=' chars other than the first will be included in the value.
def get_kv(string):
    return string.split('=', 2)

def update_last_page(request):
    request.session['last_page'] = request.get_full_path()

def get_last_page(request):
    return request.session['last_page']

# Checks that the user that made a request is an admin
def admin(request):
    return request.user.is_authenticated and request.user.profile.is_admin

# The avaiable licenses, to be displayed in the model upload form
LICENSES_FORM = {
    0: mark_safe('<a href="https://creativecommons.org/publicdomain/zero/1.0/deed.en">Creative Commons CC0 1.0 Universal Public Domain Dedication</a>'),
    1: mark_safe('<a href="https://creativecommons.org/licenses/by/4.0/deed.en">Creative Commons Attribution 4.0 International</a>, with attribution given to "3D Model Repository", and no further attribution')
}

# The same as above, for the model pages
LICENSES_DISPLAY = {
    0: mark_safe('This 3d model is made available under the <a href="https://creativecommons.org/publicdomain/zero/1.0/deed.en">Creative Commons CC0 1.0 Universal Public Domain Dedication</a>.'),
    1: mark_safe('This 3d model is licensed under the <a href="https://creativecommons.org/licenses/by/4.0/deed.en">Creative Commons Attribution 4.0 International license</a>.')
}

# The possible changes users can make to the repository
CHANGES = {
    0: 'Upload',
    1: 'Revise',
}

# The directory the models will be stored in
MODEL_DIR = '/home/tdmr/models'

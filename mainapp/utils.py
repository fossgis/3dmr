# Gets the key and value of an OSM tag from a string
# Note: any extra '=' chars other than the first will be included in the value.
def get_kv(string):
    return string.split('=', 2)

def update_last_page(request):
    request.session['last_page'] = request.get_full_path()

def get_last_page(request):
    return request.session['last_page']

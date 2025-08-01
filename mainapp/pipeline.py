def load_extra_data(backend, details, response, uid, user, *args, **kwargs):
    social = kwargs.get("social") or backend.strategy.storage.user.get_social_auth(
        backend.name, uid
    )
    if social:
        extra_data = backend.extra_data(user, uid, response, details, *args, **kwargs)
        extra_data['display_name'] = response.get('username', user.username)
        social.set_extra_data(extra_data)

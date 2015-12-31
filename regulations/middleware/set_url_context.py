class SetUrlContext(object):
    """There are multiple attributes of a request which get parsed and
    re-parsed at different levels of execution. Here we create a common store
    and stuff it inside the request object itself to be available to all
    views, templates, etc."""
    def process_view(self, request, view, args, kwargs):
        shared = request.resolver_match.kwargs.copy()
        if 'label_id' in shared:
            shared['cfr_part'] = shared['label_id'].split('-')[0]
        request.URL_CONTEXT = shared

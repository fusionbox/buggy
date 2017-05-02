def csp_middleware(get_response):
    # unsafe-inline style-src due to harvest plugin
    header_val = '; '.join([
        "default-src 'self'",
        "style-src 'self' https://fonts.googleapis.com/ 'unsafe-inline'",
        "font-src 'self' https://fonts.gstatic.com/",
        "script-src 'self' https://platform.harvestapp.com",
        "connect-src 'self' https://platform.harvestapp.com",
        "frame-src 'self' https://platform.harvestapp.com",
        "img-src 'self' https://proxy.harvestfiles.com https://cache.harvestapp.com",
    ])

    def middleware(request):
        response = get_response(request)
        response['Content-Security-Policy'] = header_val
        return response
    return middleware

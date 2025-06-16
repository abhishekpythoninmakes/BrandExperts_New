# Update your middleware.py file to handle API endpoints differently

class FixCloudflareHostMiddleware:
    """
    Middleware to fix duplicate Host headers sent by Cloudflare
    and handle API endpoint redirects
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fix duplicate host header from Cloudflare
        host = request.META.get('HTTP_HOST', '')
        if ',' in host:
            # Take the first host if there are duplicates
            request.META['HTTP_HOST'] = host.split(',')[0].strip()

        # Also fix X-Forwarded-Host if it exists
        forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST', '')
        if ',' in forwarded_host:
            request.META['HTTP_X_FORWARDED_HOST'] = forwarded_host.split(',')[0].strip()

        # Check if this is an API request
        path = request.path_info
        api_endpoints = [
            '/banners/', '/testimonials/', '/parent-categories/',
            '/dash/products/', '/api/', '/admin/api/'
        ]

        # Mark API requests to skip SSL redirect
        if any(path.startswith(endpoint) for endpoint in api_endpoints):
            request._skip_ssl_redirect = True

        response = self.get_response(request)
        return response

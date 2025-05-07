from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import redirect
from django.shortcuts import redirect

def check_access(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{request.path}?restricted=true')
        return view_func(request, *args, **kwargs)
    return wrapper

class ModalLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated and request.path.startswith('/aluno/'):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return None
            return redirect(f'/?next={request.path}')
        return None
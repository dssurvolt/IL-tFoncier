from django.shortcuts import render

def swagger_ui(request):
    """
    Sert l'interface Swagger UI.
    """
    return render(request, 'swagger.html')

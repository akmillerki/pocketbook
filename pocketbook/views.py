__author__ = 'mattmccaskey'

from django.http import HttpResponse
from django.template import Context, loader
from django.shortcuts import render, get_object_or_404

def index(request):
    context = {'index': index}
    return render(request, 'index.html', context)

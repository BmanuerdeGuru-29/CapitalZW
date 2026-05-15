"""Public Site Views"""
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactEnquiry


def home(request):
    return render(request, 'public/home.html')


def how_it_works(request):
    return render(request, 'public/how_it_works.html')


def for_suppliers(request):
    return render(request, 'public/for_suppliers.html')


def for_buyers(request):
    return render(request, 'public/for_buyers.html')


def for_financiers(request):
    return render(request, 'public/for_financiers.html')


def pricing(request):
    return render(request, 'public/pricing.html')


def contact(request):
    if request.method == 'POST':
        try:
            ContactEnquiry.objects.create(
                full_name=request.POST.get('full_name', ''),
                organisation_name=request.POST.get('organisation_name', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                organisation_type=request.POST.get('organisation_type', 'other'),
                interest_area=request.POST.get('interest_area', ''),
                message=request.POST.get('message', ''),
            )
            messages.success(request, 'Thank you! Your enquiry has been submitted. We will be in touch soon.')
            return redirect('public_site:contact')
        except Exception:
            messages.error(request, 'There was an error submitting your enquiry. Please try again.')
    return render(request, 'public/contact.html')

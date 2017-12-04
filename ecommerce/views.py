from django.contrib.auth import authenticate,login,get_user_model
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect
from .forms import ContactForm
def home_page(request):
	context={
		'title':'Home',
		'premium':'Yeahhhhhhh...'
	}
	return render(request,'home.html',context)
def about_page(request):
	context={
		'title':'About'
	}	
	return render(request,'about.html',context)
def contact_page(request):
	contact_form=ContactForm( request.POST or None)
	context={
		'title':'Contact',
		'form':contact_form,
	}
	if contact_form.is_valid():
		cd=contact_form.cleaned_data
		if request.is_ajax():
			return JsonResponse({'message':'thankyou'})
	if contact_form.errors:
		errors=contact_form.errors.as_json()
		print (errors)
		if request.is_ajax():
			return HttpResponse(errors,status=400,content_type='application/json')
	return render(request,'contact.html',context)
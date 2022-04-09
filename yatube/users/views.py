from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm, CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def user_contact(request):
    form = ContactForm(request.POST or None)
    if form.is_valid():
        ContactForm.name = form.cleaned_data['name']
        ContactForm.email = form.cleaned_data['email']
        ContactForm.subject = form.cleaned_data['subject']
        ContactForm.message = form.cleaned_data['body']
        form.save()
        return redirect('/thank-you')
    return render(request, 'contact.html', {'form': form})

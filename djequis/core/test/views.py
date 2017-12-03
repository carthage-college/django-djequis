from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from djequis.core.test.models import FooBar
from djequis.core.test.forms import FooBarForm

from djtools.utils.mail import send_mail
from djzbar.decorators.auth import portal_auth_required


@portal_auth_required(
    session_var='DJEQUIS_AUTH', redirect_url=reverse_lazy('access_denied')
)
def create_form(request):
    '''
    For more complex create views see:
    djspace/application/views.py
    djsani/insurance/views.py [informix data]
    '''

    if settings.DEBUG:
        TO_LIST = [settings.SERVER_EMAIL,]
    else:
        TO_LIST = [settings.FOOBAR_EMAIL,]
    BCC = settings.MANAGERS

    if request.method=='POST':
        form = FooBarForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.save(commit=False)
            data.created_by = request.user
            data.save()
            subject = "[Submit] {} {}".format(
                data.created_by.first_name, data.created_by.last_name
            )
            send_mail(
                request, TO_LIST, subject, data.created_by.email,
                'foobar/email.html', data, BCC
            )
            return HttpResponseRedirect(
                reverse_lazy('foobar_success')
            )
    else:
        form = FooBarForm()
    return render(
        request, 'foobar/form.html',
        {'form': form,},
    )


@portal_auth_required(
    session_var='DJEQUIS_AUTH', redirect_url=reverse_lazy('access_denied')
)
def update_form(request, fid):
    '''
    You can roll the create and update views into one to reduce redundant code.
    See:
    djforms/writingcurriculum/views.py
    djspace/application/views.py
    '''

    if settings.DEBUG:
        TO_LIST = [settings.SERVER_EMAIL,]
    else:
        TO_LIST = [settings.FOOBAR_EMAIL,]
    BCC = settings.MANAGERS

    foobar = get_object_or_404(FooBar,id=fid)
    # simple permission check
    # you can do more fine grain checks with groups. see:
    # djsani/insurance/views.py
    if foobar.created_by != request.user and not request.user.is_superuser:
        raise Http404

    if request.method=='POST':
        form =FooBarForm(
            request.POST, request.FILES, instance=foobar
        )

        if form.is_valid():
            data = form.save(commit=False)
            data.updated_by = request.user
            data.save()

            subject ="[FooBar Submission] {}: by {}, {}".format(
                foobar.title,request.user.last_name,
                request.user.first_name
            )
            send_mail(
                request, TO_LIST, subject, request.user.email,
                'foobar/email.html', {
                    'foobar':foobar,'user':request.user
                }, settings.MANAGERS
            )

            return HttpResponseRedirect(
                reverse_lazy('foobar_success')
            )
    else:
        form = FooBarForm(instance=foobar)
    return render(
        request, 'foobar/form.html',{'form': form},
    )


# the login_required decorator does the same thing as
# portal_auth_required but the latter can take an authenticated
# user from the portal and automatically sign them in here.
@login_required
def detail(request, fid):

    foobar = get_object_or_404(FooBar,id=fid)
    # simple permission check
    # you can do more fine grain checks with groups. see:
    # djsani/insurance/views.py
    if foobar.created_by != request.user and not request.user.is_superuser:
        raise Http404

    return render(
        request, 'foobar/detail.html',
        {'data':foobar},
    )

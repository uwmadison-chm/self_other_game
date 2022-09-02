from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import *
from django.core.urlresolvers import reverse
from django.conf import settings
logger = settings.LOGGER

import csv

import models
import forms

def instructions(request):
    sess = models.Session(total_trials=50, total_probings=2)
    sess.save()
    subj = models.Subject(session=sess)
    subj.save()
    request.session['subject_id'] = subj.pk
    return render_to_response("instructions.djhtml", {
        'title' : 'Welcome!',
        'subject' : subj,
        'session' : sess 
    })

def offer(request):
    s = get_object_or_404(models.Subject, pk=request.session['subject_id'])
    s_offer = s.next_choice()
    
    if s_offer is None:
        return HttpResponseRedirect(reverse(probe_preparation))
    
    if s_offer.id is None:
        # Generate numbers for this offer
        d = models.LogisticOfferDispenser(
            sigma=s.session.distribution_sigma,
            min_offer=s.session.minimum_offer,
            max_offer=s.session.maximum_offer
        )
        data = d.offer_data(s)

        s.alpha_estimate = data['regdata'][0][0]
        s.beta_estimate = data['regdata'][0][1]
        s.save()
        s_offer.self_offer = data['offers'][0]
        s_offer.other_offer = data['offers'][1]
        s_offer.save()
        
    if request.method == "POST":
        chose_self = None
        if 'choose_self' in request.POST: chose_self = True
        if 'choose_other' in request.POST: chose_self = False
        s_offer.chose_self = chose_self
        s_offer.timings = request.POST['timings']
        s_offer.save()

        return HttpResponseRedirect(reverse(offer))
    
    return render_to_response("offer.djhtml",{
        'subject' : s,
        'offers' : s_offer,
        'title' : 'Make a choice...',
    })

def probe_preparation(request):
    s = get_object_or_404(models.Subject, pk=request.session.get('subject_id'))
    
    return render_to_response("probe_preparation.djhtml",{
        "title" : "Self-Other Game: Get ready!",
        'subject' : s,
        'session' : s.session,
    })

def probe(request):
    s = get_object_or_404(models.Subject, pk=request.session.get('subject_id'))
    
    my_probe = s.next_probe()
    
    if my_probe is None:
        return HttpResponseRedirect(reverse(plot_logistic))
    
    if request.method == "POST":
        responses = my_probe.response_set.all()
        for resp in responses:
            key = "rating_%s" % (resp.question_id)
            resp.rating = float(request.POST[key])
            resp.save()
        my_probe.timing_data_json = request.POST['timings']
        my_probe.completed = True
        my_probe.save()
        return HttpResponseRedirect(reverse(probe))
        
    
    return render_to_response("probe.djhtml", {
        'title' : 'Results...',
        'probe' : my_probe,
        'subject' : s
    })

def plot_logistic(request):
    s = get_object_or_404(models.Subject, pk=request.session.get('subject_id'))

    return render_to_response("plot_logistic.djhtml",{
        'title' : 'Thanks! Here\'s your self-other plot.',
        'subject' : s,
        'session' : s.session,
    })

def plot_logistic_png(request):
    s = get_object_or_404(models.Subject, pk=request.session.get('subject_id'))
   
    canvas = s.plot_logistic()
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

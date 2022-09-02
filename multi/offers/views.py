from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import *
from django.core.urlresolvers import reverse

# For loggining
#from django.contrib import admin

import csv

import models
import forms

def beta(request):
    return render_to_response("beta.djhtml", {
        'title': 'Self-Other Game: Beta!'
    })
    
def login(request):
    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            sess_num, subj_num = request.POST['subject_number'].split("-")
            sess = models.Session.objects.get(session_number=sess_num)
            subj = sess.subject_set.get(subject_number=subj_num)
            request.session['subject_id'] = subj.pk
            if not subj.started():
                return HttpResponseRedirect(reverse(instructions))
            return HttpResponseRedirect(reverse(offer))
        
    else:
        form = forms.LoginForm()
        
    return render_to_response("login.djhtml", {
        'title' : 'Welcome!',
        'form' :  form
    })
    
def instructions(request):
    s = get_object_or_404(models.Subject, pk=request.session['subject_id'])
    return render_to_response("instructions.djhtml", {
        'title' : 'Welcome!',
        'subject' : s,
        'session' : s.session 
    })


def offer(request):
    s = get_object_or_404(models.Subject, pk=request.session['subject_id'])
    s_offer = s.next_choice()
    
#    response = HttpResponse(mimetype='text/plain')
#    response.write(s_offer)
    
#    return response
    if s_offer is None:
        return HttpResponseRedirect(reverse(probe_preparation))
#        pairings = models.ScheduledPairing.objects.all()
#        #pairings = models.Pairing.objects.filter(available_for_scheduling=True)
#        response = HttpResponse(mimetype='text/plain')
#        writer = csv.writer(response)
#        for pair in pairings:
#            if ~hasattr(pair, "probe_count"):
#                writer.writerow('foundNone')
#                
#                sp = models.ScheduledPairing.objects.create(
#                    pairing=pair,
#                    session=s.session,
#                    choice_count=s.session.default_choices_per_pairing,
#                    probing_count=s.session.default_probings_per_pairing
#                )   
#                writer.writerow(sp.probe_count)
#            else:
#                writer.writerow(pair.probe_count)
#            writer.writerow('-')
#        return response
        
#    pairing = s.random_choice_pairing()
#    if pairing is None:
#        # We can't get another choice; we're done.
#        return None
#        # return HttpResponseRedirect(reverse(probe_preparation))
#
#
#    if s_offer.id is None:
#        d = models.LogisticOfferDispenser(
#            sigma=s.session.distribution_sigma,
#            min_offer=s.session.minimum_offer,
#            max_offer=s.session.maximum_offer
#        )   
#        data = d.offer_data(s,pairing)
#        # print str(data)
#        s.alpha_estimate = data['regdata'][0][0]
#        s.beta_estimate = data['regdata'][0][1]
#        s.save()
#        s_offer.self_offer = data['offers'][0]
#        s_offer.other_offer = data['offers'][1]
#        s_offer.save()


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

def thanks(request):
    return render_to_response("thanks.djhtml", {
    'title' : 'Self-Other Game: Thanks!',
    })
    

def probe(request):
    s = get_object_or_404(models.Subject, pk=request.session.get('subject_id'))
    
    my_probe = s.next_probe()
    
    if my_probe is None:
        return HttpResponseRedirect(reverse(thanks))
    
    if request.method == "POST":
        #probe.timings = request.POST['timings']
        responses = my_probe.response_set.all()
        for resp in responses:
            key = "rating_%s" % (resp.question_id)
            resp.rating = float(request.POST[key])
            resp.save()
        my_probe.timing_data_json = request.POST['timings']
        my_probe.completed = True
        my_probe.save()
        return HttpResponseRedirect(reverse(probe))
        
    
    from django.conf import settings
    logger = settings.LOGGER

    logger.debug('my_probe.pairing: %s' % (my_probe.pairing.description ) )
    return render_to_response("probe.djhtml", {
        'title' : 'Results...',
        'probe' : my_probe,
        'pairing': my_probe.pairing.description,
        'subject' : s
    })
    

def trials_csv(request):
# WILL UPDATE LATER... Should look more like single game, but single game will change.
    response = HttpResponse(mimetype='text/plain')
    #response['Content-Disposition'] = 'attachment; filename=trials.csv'
    writer = csv.writer(response)
    header_columns = [
        'Subject number', 'Self offer', 'Other offer', 'Chose self', 'Ratio',
        'Pairing', 'Onset msec', 'Response msec'
    ]
    writer.writerow(header_columns)
    trials = models.Choice.objects.filter(chose_self__isnull=False)
    for trial in trials:
        self_int = 0
        if trial.chose_self:
            self_int = 1
        displayed, responded = ['', '']
        try:
            displayed, responded = trial.timings.split(":")
        except:
            pass
        writer.writerow([
            trial.subject.subject_number, trial.self_offer, trial.other_offer, 
            self_int, trial.ratio(), trial.pairing.description, 
            displayed, responded
        ])
    
    return response

def probes_csv(request):
# WILL UPDATE LATER... Should look more like single game, but single game will change.
    """ This view is way too damn smart. Refactor into presenter? """
    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    # First, find all of the extant questions
    questions = models.Question.objects.all()
    
    header_columns = [
        'Subject number', 'Self offer', 'Other offer', 'Chose self', 'Ratio'
    ]
    
    for q in questions:
        header_columns.append("Q%s rating" % q.id)
        header_columns.append("Q%s text" % q.id)
    header_columns.append("Timings JSON")
    writer.writerow(header_columns)
    
    probings = models.Probing.objects.filter(completed=True)
    for p in probings:
        csi = 0
        if p.choice.chose_self:
            csi = 1
        data = [
            p.subject.subject_number, p.choice.self_offer, 
            p.choice.other_offer, csi, p.choice.ratio()
        ]
        
        for q in questions:
            try:
                # Is the ORM optimizer smart enough not to n+1 this?
                resp = p.response_set.get(question=q.id)
                data.append(resp.rating)
                data.append(resp.question_text)
            except:
                # No matching question.
                data.append('')
                data.append('')
        
        data.append(p.timing_data_json)
        writer.writerow(data)
    
    return response

def plot_logistic_png(request,subject_name=None):
    sess_num, subj_num = subject_name.split("-")

    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv 

    import os  
    os.environ['HOME'] = '/var/www/apps/so_s/tmp'

    import matplotlib
    matplotlib.use("AGG")
    import matplotlib.pyplot as plt 
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from pylab import rand


    from django.conf import settings
    logger = settings.LOGGER

    s = models.Subject.objects.get(subject_number=subj_num)
    sess = models.Session.objects.get(session_number=sess_num)
    pairings = models.ScheduledPairing.objects.filter(session=sess)

    fig = plt.figure(facecolor=[1,1,1])
    for scheduled_pair in pairings:
        p = scheduled_pair.pairing
        choices_np = s.choices_numpy( p )
        lr_np = s.log_ratios_numpy( p )
        try:
            result = logistic_regression(lr_np, choices_np)
            betas = result[0]
            cov = inv(result[1])
            std_err = cov.diagonal()**0.5 # Square root of diagonal!
        except LinAlgError:
            result = 'Singular matrix'
            betas = [5,0]
            std_err = [0,0]
    
        x = numpy.arange(-8,8,.005)

        y = 1/(1+numpy.exp(betas[0]+betas[1]*x))

        #y_ci_min = 1/(1+numpy.exp((betas[0]-std_err[0])+(betas[1]+std_err[1])*x))
        #y_ci_max = 1/(1+numpy.exp((betas[0]+std_err[0])+(betas[1]-std_err[1])*x))
        y_ci_min = 1/(1+numpy.exp((betas[0]-std_err[0])+(betas[1])*x))
        y_ci_max = 1/(1+numpy.exp((betas[0]+std_err[0])+(betas[1])*x))

        basecolor = rand(3)
        facecolor_weight = numpy.array([.7,.7,.7])

        sort_lr_np = numpy.argsort(lr_np)
        smooth_window = numpy.ones(10,'d')/10
        sorted_lr_np = lr_np[sort_lr_np]
        sorted_choices_for_other = 1-choices_np[sort_lr_np]
        bin_lr_np = numpy.convolve(smooth_window,sorted_lr_np,mode='same')
        bin_choices_for_other= numpy.convolve(smooth_window,sorted_choices_for_other,mode='same')

        plt.plot(bin_lr_np,bin_choices_for_other,'bo',markerfacecolor=facecolor_weight*basecolor,markeredgewidth=0, alpha=.5)



        plt.fill_between(x,y_ci_max,y_ci_min,where=None,facecolor=facecolor_weight*basecolor,edgecolor=basecolor, alpha=.5, label='_nolegend_')
        plt.plot(x,y,'-r', color=basecolor, label=p.description)


    plt.axis([-8,8,-.6,1])
    hTitle  = plt.title ('Self-Other Plot');
    hXLabel = plt.xlabel('Ratio of SelfGets:OtherGets');
    hYLabel = plt.ylabel('Proportion of Other Choices');
    hXTics  = plt.xticks([-3,-2,-1,0,1,2,3],['20:1','7.4:1','2.7:1','1:1','1:2.7','1:7.4','1:20'] )
    plt.legend(loc='lower left')

    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

def summary_csv(request):
    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv 

    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    header_columns = ['Subject_number', 'Pairing', 'Alpha Estimate', 'Beta Estimage', 'Indifference Point' ]
    writer.writerow(header_columns)
    subjects = models.Subject.objects.all()
    for s in subjects:
        if s.finished():
            pairings = models.ScheduledPairing.objects.filter(session=s.session)
    
            for scheduled_pair in pairings:
                p = scheduled_pair.pairing
                choices_np = s.choices_numpy( p )
                lr_np = s.log_ratios_numpy( p )
                try:
                    result = logistic_regression(lr_np, choices_np)
                    betas = result[0]
                    cov = inv(result[1])
                    std_err = cov.diagonal()**0.5 # Square root of diagonal!
                except LinAlgError:
                    result = 'Singular matrix'
                    betas = [5,0]
                    std_err = [0,0]
    
                try:
                    ip = (-1*betas[0])/betas[1]
                except ZeroDivisionError:
                    ip = 0 

                if( ip > 3 ):
                    ip = 3
                elif( ip < -3 ):
                    ip = -3

                writer.writerow([s.session_and_subject, p.description, betas[0], betas[1], ip, std_err[0], std_err[1] ])
    return response

def ips_csv(request):
    from django.conf import settings
    logger = settings.LOGGER
    
    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv 

    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    header_columns = ['Subject_number', 'Pairing', 'Alpha Estimate', 'Beta Estimage', 'Indifference Point' ]
    writer.writerow(header_columns)
    subjects = models.Subject.objects.all()
    for s in subjects:
        if s.finished():
            logger.debug("Working on %s" % s.session_and_subject)
            subj_data = [s.session_and_subject]
            pairings = models.ScheduledPairing.objects.filter(session=s.session)
    
            for scheduled_pair in pairings:
                p = scheduled_pair.pairing
                logger.debug("Lookin' at %s" % p)
                choices_np = s.choices_numpy( p )
                lr_np = s.log_ratios_numpy( p )
                try:
                    result = logistic_regression(lr_np, choices_np)
                    betas = result[0]
                    cov = inv(result[1])
                    std_err = cov.diagonal()**0.5 # Square root of diagonal!
                except LinAlgError:
                    result = 'Singular matrix'
                    betas = [5,0]
                    std_err = [0,0]
    
                try:
                    ip = (-1*betas[0])/betas[1]
                except ZeroDivisionError:
                    ip = 0 

                if( sum(choices_np) < 10 ):
                    ip = -3;
                if( sum(choices_np) > 40 ):
                    ip = 3
                if( ip > 3 ):
                    ip = 3
                elif( ip < -3 ):
                    ip = -3
                subj_data += [ p.description, betas[0], betas[1], ip, std_err[0], std_err[1] ]
                logger.debug(subj_data)
            writer.writerow(subj_data)
    return response






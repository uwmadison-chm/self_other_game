from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import *
from django.core.urlresolvers import reverse
from django.conf import settings
#logger = settings.LOGGER

# For loginning
from django.contrib import admin

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
        # print str(data)
        s.alpha_estimate = data['regdata'][0][0]
        s.beta_estimate = data['regdata'][0][1]
        s.save()
        s_offer.self_offer = data['offers'][0]
        s_offer.other_offer = data['offers'][1]
        s_offer.save()
        #print "Generated (%4s, %4s) (%.3f), chose_self = %s" % (
        #    s_offer.self_offer, s_offer.other_offer, s_offer.ratio(), s_offer.chose_self
        #)
        
    if request.method == "POST":
        chose_self = None
        if 'choose_self' in request.POST: chose_self = True
        if 'choose_other' in request.POST: chose_self = False
        s_offer.chose_self = chose_self
        s_offer.timings = request.POST['timings']
        s_offer.save()
        # print "Chose (%4s, %4s) (%.3f), chose_self = %s" % (
        #     s_offer.self_offer, s_offer.other_offer, s_offer.ratio(), s_offer.chose_self
        # )
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
        
    
    return render_to_response("probe.djhtml", {
        'title' : 'Results...',
        'probe' : my_probe,
        'subject' : s
    })
    

def trials_csv(request):
    response = HttpResponse(mimetype='text/plain')
    #response['Content-Disposition'] = 'attachment; filename=trials.csv'
    writer = csv.writer(response)
    header_columns = [
        'Choice ID', 'Subject number', 'Self offer', 'Other offer', 'Chose self', 'Ratio',
        'Onset msec', 'Response msec', 'Alpha Estimate', 'Beta Estimate'
    ]
    writer.writerow(header_columns)
    trials = models.Choice.objects.filter(chose_self__isnull=False)
    funny = 0
    for trial in trials:
        # probing = trial.probings_set.all()
        self_int = 0
        if trial.chose_self:
            self_int = 1
        displayed, responded = ['', '']
        try:
            displayed, responded = trial.timings.split(":")
            subj = trial.subject
# probing.pk
# probing.paried_with_id (id?)
            writer.writerow([
                trial.pk, subj.session_and_subject, trial.self_offer, trial.other_offer, 
                self_int, trial.ratio(), displayed, responded, subj.alpha_estimate, 
                subj.beta_estimate
            ])
        except:
            funny += 1
    
    # response.write("\n%s warnings...\n" % funny)
    
    return response

def summary_csv(request):
    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv 
    import math
    logger = settings.LOGGER

    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    header_columns = ['Subject_number', 'Alpha Estimate', 'Beta Estimage', 'Indifference Point', 'Alpha SE', 'Beta SE' ]
    writer.writerow(header_columns)
    subjects = models.Subject.objects.all()
    for s in subjects:
        if s.finished():
            choices_np = s.choices_numpy()
            lr_np = s.log_ratios_numpy()
            try:
                result = logistic_regression(lr_np, choices_np)
                betas = result[0]
                cov = inv(result[1])
                std_err = cov.diagonal()**0.5 # Square root of diagonal!
            except LinAlgError:
                result = 'Singular matrix'
                betas = [5,.0001]
                std_err = [0,0]
    
            try:
                ip = (-1*betas[0])/betas[1]
            except ZeroDivisionError:
                ip = 0 

            if( ip > 3 ):
                ip = 3
            elif( ip < -3 ):
                ip = -3
            
            writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1] ] )

    return response

def probes_csv(request):
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
        subj = p.subject
        data = [
            subj.session_and_subject, p.choice.self_offer, 
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

def evolution(request):
    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv
    
    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    
    header_columns = [
        'Subject number', 'Trial number', 'Self offer', 'Other offer', 
        'Chose self', 'Alpha Estimate', 'Beta Estimate', 
        'Stderr(Alpha)', 'Stderr(Beta)'
    ]
    writer.writerow(header_columns)
    for subject in models.Subject.objects.all():
        choices_np = subject.choices_numpy()
        lr_np = subject.log_ratios_numpy()
        offers_np = subject.offers_numpy().astype(int)
        
        for i in range(len(choices_np)):
            #logger.debug("Working on subject %s trial %s" % 
            #            (subject.session_and_subject, i+1))
            try:
                result = logistic_regression(lr_np[:i+1], choices_np[:i+1])
                betas = result[0]
                cov = inv(result[1])
                std_err = cov.diagonal()**0.5 # Square root of diagonal!
            except LinAlgError:
                result = 'Singular matrix'
                betas = ['nan','nan']
                std_err = ['nan','nan']
                
            row = [
                subject.session_and_subject, i+1, offers_np[i][0], offers_np[i][1],
                int(choices_np[i]), betas[0], betas[1],
                std_err[0], std_err[1]
            ]
            writer.writerow(row)
            response.flush()
            
    return response

def plot_logistic(request,subject_name):
    sess_num, subj_num = subject_name.split("-")
    s = get_object_or_404(models.Subject, subject_number=subj_num)

    return render_to_response("plot_logistic.djhtml",{
        'title' : subject_name,
        'subject' : s,
        'session' : s.session,
    })

def plot_logistic_png(request,subject_name):
    sess_num, subj_num = subject_name.split("-")
    s = get_object_or_404(models.Subject, subject_number=subj_num)
   
    canvas = s.plot_logistic()
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
 

def plot_logistic_multiple(request, session_num=None):
    if session_num is not None:
        s = get_object_or_404(modesl.Subject.object.all() )
    else:
        s = get_object_or_404(modesl.Subject.object.all() )

    indifference_point = (-s.alpha_estimate/s.beta_estimate)
    return render_to_response("plot_logistic.djhtml",{
        "title" : subject_name,
        'subject' : s,
        'session' : s.session,
        'indifference_point' : indifference_point,
    })
    

def plot_logistic_multiple_png(request,session_name='None'):
    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv 

    import os  
    os.environ['HOME'] = '/tmp'

    import matplotlib
    matplotlib.use("AGG")
    import matplotlib.pyplot as plt 
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from pylab import rand

    try: 
        sess = models.Session.objects.get(session_number=session_name)
        subjects = sess.subject_set.all()
    except:
        subjects = models.Subject.objects.all()

    fig = plt.figure(facecolor=[1,1,1])
    for s in subjects:
        choices_np = s.choices_numpy()
        lr_np = s.log_ratios_numpy()
        try:
            result = logistic_regression(lr_np, choices_np)
            betas = result[0]
            cov = inv(result[1])
            std_err = cov.diagonal()**0.5 # Square root of diagonal!
        except LinAlgError:
            result = 'Singular matrix'
            betas = [0,0]
            std_err = [0,0]
    
        x = numpy.arange(-3,3,.005)

        y = 1/(1+numpy.exp(betas[0]+betas[1]*x))

        #y_ci_min = 1/(1+numpy.exp((betas[0]-std_err[0])+(betas[1]+std_err[1])*x))
        #y_ci_max = 1/(1+numpy.exp((betas[0]+std_err[0])+(betas[1]-std_err[1])*x))
        y_ci_min = 1/(1+numpy.exp((betas[0]-std_err[0])+(betas[1])*x))
        y_ci_max = 1/(1+numpy.exp((betas[0]+std_err[0])+(betas[1])*x))

        basecolor = rand(3)
        facecolor_weight = numpy.array([.7,.7,.7])
        plt.fill_between(x,y_ci_max,y_ci_min,where=None,facecolor=facecolor_weight*basecolor,edgecolor=basecolor, alpha=.5, label='_nolegend_')
        plt.plot(x,y,'-r', color=basecolor, label=s.subject_number)

    plt.axis([-3,3,0,1])

    hTitle  = plt.title ('Self-Other Plot');
    hXLabel = plt.xlabel('Ratio of SelfGets:OtherGets');
    hYLabel = plt.ylabel('Proportion of Other Choices');
    
    hXTics  = plt.xticks([-3,-2,-1,0,1,2,3],['20:1','7.4:1','2.7:1','1:1','1:2.7','1:7.4','1:20'] )
    plt.legend(loc='best')
    #plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, mode="expand", borderaxespad=0.)

    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

def plot_scatter_csv(request, subject_name, var_names):
    vars = var_names.split("_")
    sess_num, subj_num = subject_name.split("-")
    s = get_object_or_404(models.Subject, subject_number=subj_num)
   
    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    
    x = s.get_data( vars[0] )
    y = s.get_data( vars[1] )
    header_columns = [
        vars[0], vars[1],
    ]
    if len(vars) > 2:
        z = s.get_data(vars[2])
        header_columns = [header_columns, vars[2] ]

    # THIS WILL SOMEDAY WRITE...
    writer.writerow(header_columns)
    response.flush()
            
    return response

def plot_scatter_png(request, subject_name, var_names):
    vars = var_names.split("_")
    sess_num, subj_num = subject_name.split("-")
    s = get_object_or_404(models.Subject, subject_number=subj_num)
   
    x = s.get_data( vars[0] )
    y = s.get_data( vars[1] )

    import os  
    os.environ['HOME'] = '/var/www/apps/so_s/tmp'
    from scipy.stats import linregress
    from numpy import vstack
    import matplotlib
    matplotlib.use("AGG")
    import matplotlib.pyplot as plt 
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    
    fig = plt.figure(facecolor=[1,1,1])
    #plt.grid(color=[.95,.95,.8], linestyle='--', linewidth=1)

    lin_fit = linregress(x,y)

    if len(vars) > 2:
        z = s.get_data(vars[2])
        z = (z-z.min())/(z.max()-z.min())
        dot_colors = vstack((z*.1,z*.1,z))
        dot_colors = dot_colors.T
    else:
        dot_colors = [.8, .7, .5]
    
    #plt.plot( x, y, 'bo', markerfacecolor=[.8, .7, .5], markeredgecolor=[0,0,0], alpha=.5)
    plt.scatter( x, y, s=20, c=dot_colors, alpha=.5)
    plt.plot( x, lin_fit[1]+lin_fit[0]*x, '-', color=[1, .4, .4], linewidth=2)
    
    my_title = 'r=' + str(lin_fit[2]) + ', p=' + str(lin_fit[3])
    hTitle  = plt.title ( my_title )
    hXLabel = plt.xlabel( vars[0] )
    hYLabel = plt.ylabel( vars[1] )

    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
    
def ips_csv(request):
    from logreg import logistic_regression
    import numpy
    from scipy.linalg import LinAlgError
    from scipy.linalg import inv 
    import math 


    response = HttpResponse(mimetype='text/plain')
    writer = csv.writer(response)
    header_columns = ['Subject_number', 'Alpha Estimate', 'Beta Estimage', 'Indifference Point', 'Alpha SE', 'Beta SE']
    writer.writerow(header_columns)
    subjects = models.Subject.objects.all()
    for s in subjects:
        if s.finished():
            choices_np = s.choices_numpy()
            lr_np = s.log_ratios_numpy()
            try:
                result = logistic_regression(lr_np, choices_np)
                betas = result[0]
                cov = inv(result[1])
                std_err = cov.diagonal()**0.5 # Square root of diagonal!
            except LinAlgError:
                result = 'Singular matrix'
                betas = [5,.0001]
                std_err = [0,0]
    
            try:
                ip = (-1*betas[0])/betas[1]
            except ZeroDivisionError:
                ip = 0 

            if( sum(choices_np) > 180 ):
                ip = 3 
            if( sum(choices_np) < 20 ):
                ip = -3; 

            if( ip > 3 ):
                ip = 3
            elif( ip < -3 ):
                ip = -3

            writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1]] )

    return response

    


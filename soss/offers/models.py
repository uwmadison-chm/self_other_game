from django.db import models
from django.conf import settings
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import views

import random as native_random

import numpy
from numpy import random
from logreg import logistic_regression

import urllib2
from urllib2 import urlopen

logger = settings.LOGGER

# A base that everything should inherit from -- includes columns for
# timestamps and SCM data.
class StampedTrackedModel(models.Model):
    # Timestamp columns
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # And the scm_revision
    scm_revision = models.CharField(
        "SCM Revision", max_length=255, default=settings.REPOSITORY_URL, editable=False)

    class Meta:
        abstract = True

class Session(StampedTrackedModel):
    
    session_number = models.IntegerField(unique=True)
    session_date = models.DateField(blank=True, editable=False)
    total_trials = models.IntegerField(default=200)
    total_probings = models.IntegerField(default=2)
    distribution_sigma = models.FloatField(default=0.25)
    minimum_offer = models.IntegerField(default=1)
    maximum_offer = models.IntegerField(default=1000)
    
    def __unicode__(self):
        return "%03u: %s" % (self.session_number, self.session_date)
    
    @property
    def session_number_ext(self):
        return "%03u" % (self.session_number)
    
    def save(self, force_insert=False, force_update = False):
        creating = (self.pk is None)
        subject_url = str(settings.SUBJECT_SPINDLER_BASE)+("/%s.js" % (self.session_number))
        fd = urlopen(subject_url)
        session_data = json.loads(fd.read())
        fd.close()
        
        self.session_date = session_data.get("session_date")
        super(Session, self).save(force_insert, force_update)
        if creating:
            for sn in session_data.get("subjects"):
                self.subject_set.create(subject_number=sn)
        
    def completed_subjects(self):
        return [s for s in self.subject_set.all() if s.finished() ]
        
    def incomplete_subjects(self):
        return [s for s in self.subject_set.all() if not s.finished() ]
    
    def pending_subjects(self):
        return [s for s in self.subject_set.all() if s.pending() ]
    
    def pending_count(self):
        return len(self.pending_subjects())
    
    def ready_for_payout(self):
        return len(self.incomplete_subjects()) == 0
        
    
    def compute_payouts(self):
        for subject in self.completed_subjects():
            logger.debug("Computing payouts for %s" % subject.session_and_subject)
            subject.compute_payouts()
            subject.save()
    
    def payout_readiness_message(self):
        msg = "No one has started playing yet"
        if len(self.pending_subjects()) > 0:
            msg = "%s still playing" % len(self.pending_subjects())
        elif len(self.completed_subjects()) > 0:
            msg = "Everyone is done! Ready to compute."
        return msg

class Subject(StampedTrackedModel):
    """A subject scheduled for testing."""
    subject_number = models.CharField(max_length=10)

    # These will be empty until the subjects start running
    alpha_estimate = models.FloatField(default=0.0)
    beta_estimate = models.FloatField(default=0.0)
    
    session = models.ForeignKey('Session')
    
    computed_amount = models.DecimalField(
        blank=True, null=True, max_digits=5, decimal_places=2)
    
    paid_amount = models.DecimalField(
        blank=True, null=True, max_digits=5, decimal_places=2)

    # Method time!
    def __unicode__(self):
        return self.subject_number
    
    @property
    def session_and_subject(self):
        return "%s-%s" % (self.session.session_number_ext, self.subject_number)
    
    class Meta:
        unique_together = (('session', 'subject_number'))
            
    def choices_numpy(self):
        return numpy.array([
            c.chose_self for c in self.completed_choices()
        ]).astype(float)
    
    def pk_numpy(self):
        return numpy.array([
            c.pk for c in self.completed_choices()
        ]).astype(float)

    def trial_numpy(self):
        t = self.pk_numpy()
        return t - t.min() + 1
    
    def rt_numpy(self):
        return numpy.array([
            c.rt() for c in self.completed_choices()
        ]).astype(float)
    
    def offers_numpy(self):
        return numpy.array([
            (c.self_offer, c.other_offer) for c in self.completed_choices()
        ]).astype(float)

    def offers_self_numpy(self):
        return self.offers_numpy()[:,0]
            
    def offers_other_numpy(self):
        return self.offers_numpy()[:,1]
    
    def ratios_numpy(self):
        choices = self.completed_choices()
        if len(choices) < 1:
            return numpy.array(()).astype(float)
        return numpy.array([c.ratio() for c in choices])
        
    def log_ratios_numpy(self):
        return numpy.log(self.ratios_numpy())
    
    def log_rt_numpy(self):
        return numpy.log(self.rt_numpy())

    def betas_numpy(self):
        return numpy.array(
            (self.alpha_estimate, self.beta_estimate)
        ).astype(float)
    
    @property
    def indifference_point(self):
        try:
            ip = (-1*self.alpha_estimate)/self.beta_estimate
        except ZeroDivisionError:
            ip = 0 

        if( ip > 3 ):
            ip = 3
        elif( ip < -3 ):
            ip = -3
        
        return ip
    
    def diagnostic_links(self):
        return ''
        #return mark_safe("<a href=\"%s\">Logistic</a> &middot; <a href=\"%s\">Scatter</a>" % (
        #    reverse(views.plot_logistic_png, args=[self.session_and_subject]),
        #    reverse(views.plot_scatter_png, kwargs={'subject_name':self.session_and_subject, 'var_names':'logratio_trial_choseSelf'}) ))
    diagnostic_links.allow_tags = True
    
    def session_diagnostic_link(self):
        return ''
        #return mark_safe("<a href=\"%s\">Session Logistic</a>" % ( 
        #    reverse(views.plot_logistic_multiple_png, args=[self.session.session_number_ext])))
    session_diagnostic_link.allow_tags = True
            
    def completed_choices(self):
        try:
            return self.choice_set.filter(chose_self__isnull=False).order_by('id')
        except:
            return []
    
    def finished(self):
        return (self.next_choice() is None and self.next_probe() is None)
        
    def started(self):
        return self.choices_count() > 0
    
    def pending(self):
        return self.started() and not self.finished()
    
    def choices_count(self):
        return self.choice_set.count()
    
    def probes_count(self):
        return self.probing_set.count()

    def current_choice(self):
        choices = self.choice_set.filter(chose_self=None)
        if len(choices) == 0:
            return None
        return choices[0]

    def next_choice(self):
        """
        Return the next choice the subject must make, or None if
        the subject has already made total_trials choices.
        """
        choice = self.current_choice()

        if choice is None:
            choice = Choice()
            choice.subject = self
            if self.choice_set.count() >= self.session.total_trials:
                choice = None
                # Ends this.
        return choice
    
    def next_probe(self):
        """ 
        Find the associated uncompleted probe, if it exists. 
        Otherwise, if possible, build a new probe associated with a
        random choice.
        Return None if we can't do that, either -- in the case where the
        subject has completed_probes().count() >= total_probings, or there
        isn't a remaining unprobed choice.
        """
        if self.completed_probes().count() >= self.session.total_probings:
            # We're unambiguously done.
            return None
        try:
            # MultipleObjectsReturned is a serious error we can't catch
            return self.current_probe()
        except Probing.DoesNotExist:
            # This isn't a big deal, though.
            pass
        
        try:
            c = self.random_unprobed_choice()
        except IndexError:
            return None # No unprobed choice, can't continue!
        p = Probing(subject=self, choice=c)
        p.save()
        # Also create Reponses related to this probing
        questions = Question.objects.filter(active=True)
        for q in questions:
            r = Response(question=q, probing=p, question_text=q.question_text)
            r.save()
        return p
        
    def current_probe(self):
        probes = self.probing_set.filter(completed = False)
        if len(probes) > 0:
            return probes[0]
        else:
            return self.probing_set.get(completed = False)
    
    def completed_probes(self):
        return self.probing_set.filter(completed=True)
    
    def unprobed_choices(self):
        return self.choice_set.filter(probing=None)
    
    def random_unprobed_choice(self):
        return self.unprobed_choices().order_by('?')[0]
    
    def pair_probings(self):
        count = 0
        for probe in self.completed_probes().filter(paired_with__isnull=True):
            probe.pair_with_eligible_probe()
            probe.save()
            probe.paired_with.save()
            count += 1
        return count
    
    def compute_payouts(self):
        # self.pair_probings()
        amount = 2000
        for my_probe in self.completed_probes():
            # paired_probe = my_probe.paired_with_me
            
            # logger.debug("this probe: %s -- paired probe %s" % (my_probe, paired_probe))
            logger.debug("this probe: %s " % (my_probe))
            # if my_probe.choice and paired_probe and paired_probe.choice:
            if my_probe.choice:
                amount_from_self = my_probe.amount_for_self
                # amount_from_other = paired_probe.amount_for_other
                # amount = (
                #     amount + 
                #     amount_from_self + 
                #     amount_from_other )
                amount = (
                    amount - 
                    amount_from_self )
                #logger.debug(
                #    "Adding %s from self and %s from other. Total: %s" % (
                #    amount_from_self, 
                #    amount_from_other,
                #    amount)
                #)
                logger.debug(
                    "Subtracting %s from self. Total: %s" % (
                    amount_from_self, 
                    amount)
                )
            else:
                logger.debug("Can't find one of the important bits here.")
            
        self.computed_amount = "%.2f" % (amount/100.0,)
        return self.computed_amount
        
    def inlined(self):
        ready_text = "Not ready for payout"
        if self.finished():
            ready_text = "Ready for payout"
        return (
            "%s - Trial %s of %s - Probing %s of %s - %s" %
            (
            self.session_and_subject, 
            self.completed_choices().count(), self.session.total_trials, 
            self.completed_probes().count(), self.session.total_probings,
            ready_text
            )
        )

    def plot_logistic(self):
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

        fig = plt.figure(facecolor=[1,1,1])

        choices_np = self.choices_numpy()
        lr_np = self.log_ratios_numpy()
        try:
            result = logistic_regression(lr_np, choices_np)
            betas = result[0]
            cov = inv(result[1])
            std_err = cov.diagonal()**0.5 # Square root of diagonal!
        except LinAlgError:
            result = 'Singular matrix'
            betas = ['0','0']
            std_err = ['0','0']
        
        x = numpy.arange(-3,3,.005)
        y = 1/(1+numpy.exp(betas[0]+betas[1]*x))

        y_ci_min = 1/(1+numpy.exp((betas[0]-std_err[0])+(betas[1]+std_err[1])*x))
        y_ci_max = 1/(1+numpy.exp((betas[0]+std_err[0])+(betas[1]-std_err[1])*x))

        sort_lr_np = numpy.argsort(lr_np)
        smooth_window = numpy.ones(10,'d')/10
        sorted_lr_np = lr_np[sort_lr_np]
        sorted_choices_for_other = 1-choices_np[sort_lr_np]
        bin_lr_np = numpy.convolve(smooth_window,sorted_lr_np,mode='same')
        bin_choices_for_other= numpy.convolve(smooth_window,sorted_choices_for_other,mode='same')

        plt.plot(bin_lr_np,bin_choices_for_other,'bo',markerfacecolor=[.65, .65, .9],markeredgewidth=0)
        plt.fill_between(x,y_ci_max,y_ci_min,where=None,facecolor=[1,.85,.85],edgecolor=[1,.65,.65], alpha=.85)

        plt.plot(x,y,'r')

        hTitle  = plt.title (''.join(['Self-Other Plot for subject ', self.subject_number]));
        hXLabel = plt.xlabel('Ratio of SelfGets:OtherGets');
        hYLabel = plt.ylabel('Proportion of Other Choices (per 10 choices)');
        
        hXTics  = plt.xticks([-3,-2,-1,0,1,2,3],['20:1','7.4:1','2.7:1','1:1','1:2.7','1:7.4','1:20'] )


        canvas_plot=FigureCanvas(fig)
        return canvas_plot
#        response=django.http.HttpResponse(content_type='image/png')
#        canvas.print_png(response)
#        return response

    def get_data( self, var_name=None ):
        var_lookup = {
            'rt': self.rt_numpy,
            'logrt': self.log_rt_numpy,
            'choseSelf': self.choices_numpy,
            'trial': self.trial_numpy,
            'offerSelf': self.offers_self_numpy,
            'offerOther': self.offers_other_numpy,
            'selfOffer': self.offers_self_numpy,
            'otherOffer': self.offers_other_numpy,
            'ratio': self.ratios_numpy,
            'logratio': self.log_ratios_numpy,
        }
        if var_name is not None:
            return var_lookup[var_name]()
        else:
            return None
    
class Choice(StampedTrackedModel):
    subject = models.ForeignKey('Subject')
    """A single offer / response pair."""
    self_offer = models.IntegerField()
    other_offer = models.IntegerField()
    # This field will be true before a question was answered. A subject
    # should never have more than one choice with a blank chose_self.
    chose_self = models.NullBooleanField()
    
    timings = models.TextField(blank=True)

    class Meta:
        ordering = ['subject', 'id']
    
    def __unicode__(self):
        return "Choice for subject %s (%s:%s)" % (
            self.subject.subject_number, self.self_offer, self.other_offer)
    
    def ratio(self):
        return float(self.other_offer)/self.self_offer

    def rt(self):
        displayed, responded = ['', '']
        displayed, responded = self.timings.split(":")
        return numpy.subtract(float(responded),float(displayed))
    
    # Return none if there's no choice made yet
    # If we're looking for a self offer and the subject chose self,
    # return the self offer.
    # If we're looking for an other offer and the subject chose other, 
    # return the other offer.
    # Otherwise, return 0.
    def _amount_for_player(self, for_self):
        ret = None
        if self.chose_self is not None:
            ret = 0
            if (for_self and self.chose_self):
                ret = self.self_offer
            elif (not for_self and not self.chose_self):
                ret = self.other_offer
    
        return ret
    
    @property
    def amount_for_self(self):
        return self._amount_for_player(True)
    
    @property
    def amount_for_other(self):
        return self._amount_for_player(False)
            
class Question(StampedTrackedModel):
    question_text = models.TextField()
    active = models.BooleanField(default=True)
    order = models.IntegerField()

    class Meta:
        ordering = ['-active', 'order', 'id']
    
    def __unicode__(self):
        return "%s ( %s, %s )" % (self.question_text, self.order, self.active)

class Probing(StampedTrackedModel):
    subject = models.ForeignKey('Subject')
    choice = models.ForeignKey('Choice')
    paired_with = models.ForeignKey('Probing', unique=True, blank=True, null=True)
    
    timing_data_json = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    
    def eligible_pairings(self):
        # This is gonna be:
        # It belongs to a different completed subject in the same session
        # It's not yet paired
        subject_ids = [
            s.pk for s in self.subject.session.subject_set.all()
            if (s.pk != self.subject.pk and s.finished())
        ]
        if len(subject_ids) == 0: return None
        logger.debug("Subjects: found %s" % subject_ids)
        # Now we can use that subject list to find a probing

        probings = Probing.objects.filter(
            choice__subject__in=subject_ids ).filter(
            completed=True ).filter(
            paired_with__isnull=True )
        
        return probings
            
        
    def random_eligible_pairing(self):
        probings = self.eligible_pairings().order_by("?")
        logger.debug("%s eligible left" % probings.count())
        probe = probings[0]
        
        logger.debug("Probing found %s" % probe.pk)
        return probe
        
    def pair_with_eligible_probe(self):
        if self.paired_with_me is not None: return
        ep = self.random_eligible_pairing()
        logger.debug("Pairing %s and %s" % (self, ep))
        ep.paired_with = self
        self.paired_with = ep
        
    def response_data_for_form(self):
        return [ { 'question_id': resp.question_id, 'rating':resp.rating }
            for resp in self.response_set.all()
        ]
        
    def get_paired_with_me(self):
        try:
            return Probing.objects.get(paired_with=self)
        except Probing.DoesNotExist:
            return None
    paired_with_me=property(get_paired_with_me)
    
    @property
    def amount_for_self(self):
        return self.choice.amount_for_self
    
    @property
    def amount_for_other(self):
        return self.choice.amount_for_other
    
    class Meta:
        ordering = ['subject', 'id']
    
    def __unicode__(self):
        return ("Probing: id: %s, choice_id: %s, paired_with_id: %s, completed: %s" % 
            (self.pk, self.choice_id, self.paired_with_id, self.completed, ))
    
class Response(StampedTrackedModel):
    question = models.ForeignKey('Question')
    probing = models.ForeignKey('Probing')
    rating = models.FloatField(default=50)
    
    #not normalized; that's OK. 
    question_text = models.TextField(blank=True)
    
    class Meta:
        ordering = ['probing', 'question', 'id']
      
class LogisticOfferDispenser(object):
    
    """ 
    Uses logistic regression to compute new pairs of financial offers
    designed to find the point at which a subject has a .5 chance of acceping.
    """
    
    def __init__(self, sigma = 1.0, min_offer = 1, max_offer = 1000):
        super(LogisticOfferDispenser, self).__init__()
        self.sigma = sigma
        self.min_offer = min_offer
        self.max_offer = max_offer
        self.max_log_ratio = numpy.log10(float(max_offer) / min_offer)
    
    # Makes an indifference point that's 0 if choices' mean is < 0.5,
    # infinite if choices' mean is > 0.5, and 1 otherwise.
    def vote_bounds(self, choices):
        ip = 1.0
        avg = numpy.mean(choices) # This is nan if choices is empty.
        if (avg < 0.5):
            ip = 0
        if (avg > 0.5): # Both are false for nan
            ip = numpy.inf
        return ip
    
    # Caps an indifference point to 
    def make_ip_in_bounds_with_vote(self, indifference_point, choices):
        max_bound = 10**self.max_log_ratio
        min_bound = 10**-self.max_log_ratio
        safe_ip = indifference_point
        # Hack to prevent very early algorithmic craziness
        if len(choices) <= 4: safe_ip = 1.0
        
        if safe_ip >= min_bound and safe_ip <= max_bound:
            pass
        else:
            safe_ip = self.vote_bounds(choices)
        
        return safe_ip
            
    def offer_data(self, subject):
        ratios = subject.log_ratios_numpy()
        choices = subject.choices_numpy()
        
        regression_data = self.regress(ratios, choices)
        betas = regression_data[0]
        original_ip = self.indifference_point(betas[0], betas[1])
        ip = self.make_ip_in_bounds_with_vote(
            original_ip,
            choices
        )
        logger.debug("Estimated IP: %s Capped IP: %s" % (original_ip, ip))
        next_log_ratio = self.next_log_ratio(ip)
        offers = self.random_offers_from_ratio(next_log_ratio)
        
        return {
            'regdata' : regression_data,
            'next_log_ratio' : next_log_ratio,
            'offers' : offers
        }
    
    def convert_and_cap_ratio(self, log_ratio):
        capped = min(self.max_log_ratio, max(-self.max_log_ratio, log_ratio))
        return 10**capped
    
    # Plan:
    # 1: Get a ratio in non-log space
    # 2: [self, other] = [1, ratio]
    # 3: c_min = min_offer/min(self, other)
    # 4: c_max = max_offer/max(self, other)
    # 5: const ~ U(c_min, c_max)
    # 6: [self, other] *= const
    # 7: Round self, other. Clip if rounded out of bounds?
    def random_offers_from_ratio(self, log_ratio):
        ratio = self.convert_and_cap_ratio(log_ratio)
        # Remember: self_offer starts as 1; ratio can be from .001..1000
        const_min = float(self.min_offer)/min(1, ratio)
        const_max = float(self.max_offer)/max(1, ratio)
        const = numpy.random.uniform(const_min, const_max)
        self_offer = int(numpy.round(1*const))
        other_offer = int(numpy.round(ratio*const))
        logger.debug("log_ratio: %s ratio: %s const_min: %s, const_max %s, const: %s, self: %s, other %s" %
            (log_ratio, ratio, const_min, const_max, const, self_offer, other_offer))
        return (self_offer, other_offer)
    
    def indifference_point(self, alpha, beta):
        return numpy.exp(-alpha/beta)
    
    def next_log_ratio(self, indifference_estimate):
        log_ip = numpy.log10(indifference_estimate)
        # If we're waaaaay off the map, choose something around 0.
        if log_ip > self.max_log_ratio:
            log_ip = self.max_log_ratio
        elif log_ip < -self.max_log_ratio:
            log_ip = -self.max_log_ratio
            
        if numpy.random.uniform(0,1) < .5:
            log_ip = 0

        return numpy.random.normal(log_ip, self.sigma)
        
    def regress(self, log_ratios, choices, beta_estimate = numpy.array([0.0, 0.0])):
        # Return the whole enhchilada
        return logistic_regression(log_ratios, choices, beta_estimate)
        


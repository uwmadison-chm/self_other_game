from django.db import models
from django.conf import settings
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
# import views

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
    default_choices_per_pairing = models.IntegerField(default=50)
    default_probings_per_pairing = models.IntegerField(default=2)
    distribution_sigma = models.FloatField(default=.25)
    minimum_offer = models.IntegerField(default=1)
    maximum_offer = models.IntegerField(default=1000)
    total_trials = models.IntegerField(default=200)
    total_probings = models.IntegerField(default=10)

    
    def __unicode__(self):
        return "%03u: %s" % (self.session_number, self.session_date)

    @property
    def session_number_ext(self):
        return "%03u" % (self.session_number)
    
    def save(self, force_insert=False, force_update = False):
        creating = (self.pk is None)
#        if not creating:
#            return
            
        subject_url = str(settings.SUBJECT_SPINDLER_BASE)+("/%s.js" % (self.session_number))
        fd = urlopen(subject_url)
        session_data = json.loads(fd.read())
        fd.close()
        
        self.session_date = session_data.get("session_date")
        super(Session, self).save(force_insert, force_update)
        if creating:
            for sn in session_data.get("subjects"):
                logger.debug("Auto-creating subject %s" % sn)
                self.subject_set.create(subject_number=sn)
            
            for pair in Pairing.objects.filter(available_for_scheduling=True):
                sp = ScheduledPairing.objects.create(
                    pairing=pair,
                    session=self,
                    choice_count=self.default_choices_per_pairing,
                    probing_count=self.default_probings_per_pairing
                )
                logger.debug("Scheduled pairing %s" % sp)

    def completed_subjects(self):
        return [s for s in self.subject_set.all() if s.finished() ]

    def imcomplete_subjects(self):
        return [s for s in self.subject_set.all() if not s.finished() ]

    def pending_subjects(self):
        return [s for s in self.subject_set.all() if s.pending() ];

    def pending_count(self):
        return len(self.pending_subjects())

    def ready_for_payout(self):
        return len(self.incomplete_subjects())

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
    
class PairingManager(models.Manager):
    def get_available_pairing(self, subject, countable_name):
        countable_mapping = {
            "choice": ("choice_count", "offers_choice"),
            "probing": ("probing_count", "offers_probing"),
        }
        max_field, count_table = countable_mapping[countable_name]
        # This makes me nervous: we're at the hairy edge of query syntax.
        query = """
        SELECT * FROM (SELECT 
                osp.pairing_id, 
                osp.%s AS countable_max,
                (SELECT COUNT(*) FROM %s AS t_count WHERE t_count.pairing_id = osp.pairing_id AND t_count.subject_id = %s) AS made_offers
        FROM offers_scheduledpairing AS osp
        WHERE osp.session_id = %s) AS countenings
        WHERE countable_max > made_offers
        ORDER BY RANDOM()
        """ % (max_field, count_table, "%s", "%s")
         # Yes, I just replaced a %s with another %s for feeding to SQL
         
        from django.db import connection
        cursor = connection.cursor()
        try:
            cursor.execute(query, [subject.pk, subject.session.pk])
            row = cursor.fetchone()
            logger.debug("Potential pairing: %s" % (str(row)))
            return self.model.objects.get(pk=row[0])
        except:
            # logger.debug(query)
            return None

class Pairing(StampedTrackedModel):
    
    description = models.CharField(max_length=255)
    available_for_scheduling = models.BooleanField(default=True)
    objects = models.Manager()
    locator = PairingManager()
    
    def __unicode__(self):
        return "%u: %s" % (self.pk, self.description)

class ScheduledPairing(StampedTrackedModel):
    
    choice_count = models.IntegerField(default=40)
    probing_count = models.IntegerField(default=2)
    
    pairing = models.ForeignKey("Pairing")
    session = models.ForeignKey("Session")
    
    def __unicode__(self):
        return "Session %s, Pairing %s (%s/%s)" % (self.session, self.pairing, self.choice_count, self.probing_count)

class Subject(StampedTrackedModel):
    """A subject scheduled for testing."""
    subject_number = models.CharField(max_length=10)

    # These will be empty until the subjects start running
    #alpha_estimate = models.FloatField(default=0.0)
    #beta_estimate = models.FloatField(default=0.0)
    
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
     
    def diagnostic_link(self):
        return mark_safe("<a href=\"%s\">Subject Diagnostics</a>" % (
            reverse(views.plot_logistic_png, args=[self.session_and_subject])))
    diagnostic_link.allow_tags = True

    def random_choice_pairing(self):
        return Pairing.locator.get_available_pairing(self, "choice")
    
    def random_probing_pairing(self):
        return Pairing.locator.get_available_pairing(self, "probing")
        
    def choices_numpy(self, pairing = None):
        return numpy.array([
            c.chose_self for c in self.completed_choices(pairing)
        ]).astype(float)
    
    def offers_numpy(self, pairing = None):
        return numpy.array([
            (c.self_offer, c.other_offer) for c in self.completed_choices(pairing)
        ]).astype(float)
    
    def ratios_numpy(self, pairing = None):
        choices = self.completed_choices(pairing)
        if len(choices) < 1:
            return numpy.array(()).astype(float)
        return numpy.array([c.ratio() for c in choices])
        
    def log_ratios_numpy(self, pairing = None):
        return numpy.log(self.ratios_numpy(pairing))
    
    def completed_choices(self, pairing=None):
        if pairing is not None:
            try:
                filtered_choices = self.choice_set.filter(chose_self__isnull=False).filter(pairing=pairing)
                return filtered_choices.order_by('id')
            except:
                return []
        else:
            try:
                filtered_choices = self.choice_set.filter(chose_self__isnull=False)
#            if pairing is not None:
#                filtered_choices = filtered_choices.filter(pairing=pairing)
                return filtered_choices.order_by('id')
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

        if choice is  None:
            # Let's actually make a proper new choice and ditch the crap in
            # the view, OK?
            # Choices need a Pairing and an Offer...
            pairing = self.random_choice_pairing()
            if pairing is None:
                # We can't get another choice; we're done.
                return None
            
            d = LogisticOfferDispenser(
                sigma=self.session.distribution_sigma,
                min_offer=self.session.minimum_offer,
                max_offer=self.session.maximum_offer
            )
            data = d.offer_data(self, pairing)
            logger.debug(data)
            choice = Choice.objects.create(
                subject=self, 
                pairing=pairing,
                self_offer=data['offers'][0],
                other_offer=data['offers'][1],
            )
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

        pairing = self.random_probing_pairing()
        # This means we're done
        if pairing is None: return None
           
        choice = self.random_unprobed_choice(pairing)
        # This also means we're done
        if choice is None: return None
            
        p = Probing.objects.create(
            subject = self,
            choice = choice,
            pairing = pairing
        )
#        try:
#            c = self.random_unprobed_choice()
#        except IndexError:
#            return None # No unprobed choice, can't continue!
#        p = Probing(subject=self, choice=c)
        logger.debug("probing: %s" % ( p ) );
        p.save()
        # Also create Reponses related to this probing
        questions = Question.objects.filter(active=True)
        for q in questions:
            r = Response(question=q, probing=p, question_text=q.question_text)
            r.save()
        return p
    
#    def next_probing(self):
#        """ 
#        Find the associated uncompleted probe, if it exists. 
#        Otherwise, if possible, build a new probe associated with a
#        random choice.
#        Return None if we can't do that, either -- in the case where the
#        subject has completed_probes().count() >= total_probings, or there
#        isn't a remaining unprobed choice.
#        """
#        
#        probing = self.current_probing()
#        if probing is None:
#            pairing = self.random_probing_pairing()
#            # This means we're done
#            if pairing is None: return None
#            
#            choice = self.random_unprobed_choice(pairing)
#            # This also means we're done
#            if choice is None: return None
#            
#            probing = Probing.objects.create(
#                subject = self,
#                choice = choice,
#                pairing = pairing
#            )
#
#        # Also create Reponses related to this probing
#        for q in Question.objects.filter(active=True):
#            r = Response.objects.create(
#                question=q, probing=probing, question_text=q.question_text)
#        return probing
        
    def current_probe(self):
        probes = self.probing_set.filter(completed = False)
        if len(probes) > 0:
            return probes[0]
        else:
            return self.probing_set.get(completed = False)
#    def current_probing(self):
#        try:
#            return self.probing_set.get(completed=False)
#        except Probing.DoesNotExist:
#            return None
    
#    def completed_probes(self):
#        return self.probing_set.filter(completed=True)
    def completed_probes(self, pairing=None):
        probes = self.probing_set.filter(completed=True)
        if pairing is not None: probes = probes.filter(pairing=pairing)
        return probes
    
#    def unprobed_choices(self):
#        return self.choice_set.filter(probing=None)
    def unprobed_choices(self, pairing=None):
        choices = self.choice_set.filter(probing=None)
        if pairing is not None: choices = choices.filter(pairing=pairing)
        return choices
    
    def random_unprobed_choice(self, pairing=None):
        return self.unprobed_choices(pairing).order_by('?')[0]    
    
    def compute_payouts(self):
        amount = 0
        for my_probe in self.completed_probes():
            logger.debug("this probe: %s " % (my_probe))
            
            if my_probe.choice:
                amount_from_self = my_probe.amount_for_self
                amount = (amount + amount_from_self )
                logger.debug( "Adding %s from self. Total: %s" % (
                    amount_from_self,
                    amount))
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


class Choice(StampedTrackedModel):
    """A single offer / response pair."""
    subject = models.ForeignKey('Subject')
    pairing = models.ForeignKey('Pairing')
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

    def _amount_for_player(self,for_self):
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
        return self.amount_for_player(False)

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
    pairing = models.ForeignKey('Pairing')
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
        return ("Probing: id: %s, choice_id: %s, pairing_id: %s, paired_with_id: %s, completed: %s" %
            (self.pk, self.choice_id, self.pairing_id, self.paired_with_id, self.completed, ))
    
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


    def offer_data(self, subject, pairing):
        from scipy.linalg import LinAlgError

        ratios = subject.log_ratios_numpy(pairing)
        choices = subject.choices_numpy(pairing)

        logger.debug( "OFFERS_DATA: choices %s, len(choices): %s" % (choices, len(choices) ) )

        # THIS IS STUPID... when the array is empty it isn't an array... ?
        #   why is the len(array([], dtype=float64)) == 1, but ?
        # ratios = numpy.array(ratios)
        # choices = numpy.array(choices).transpose()
        # choices = numpy.array(choices)
        # if choices.shape[-1] == 0:
        #     choices = numpy.array(())
        logger.debug( "choices %s, len(choices): %s" % (choices, len(choices)) )
        logger.debug( "ratios %s, shape (ratios): %s" % (ratios, ratios.shape[-1]) )

        try: 
            regression_data = self.regress(ratios, choices)
            betas = regression_data[0]
        except LinAlgError:
            regression_data = []
            betas = [0,1]
        original_ip = self.indifference_point(betas[0], betas[1])
        ip = self.make_ip_in_bounds_with_vote( original_ip, choices )
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
        

    def random_offers_from_ratio(self,log_ratio):
        ratio = self.convert_and_cap_ratio(log_ratio)

        const_min = float(self.min_offer)/min(1,ratio)
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
        logger.debug("Current estimate: %s" % indifference_estimate)
        log_ip = numpy.log10(indifference_estimate)
        # If we're waaaaay off the map, choose something around 0.
        if log_ip > self.max_log_ratio:
            log_ip = self.max_log_ratio
        elif log_ip < -self.max_log_ratio:
            log_ip = -self.max_log_ratio

        # this next line makes half the offers from ~N(1:1,sigma)
        if numpy.random.uniform(0,1) < .5:
            log_ip = 0
            
        return numpy.random.normal(log_ip, self.sigma)
        
    def regress(self, log_ratios, choices, beta_estimate = numpy.array([0.0, 0.0])):
        # Return the whole enhchilada

        logger.debug( "log_ratios %s, shape (log_ratios): %s, dtype: %s" % (log_ratios, log_ratios.shape[-1], log_ratios.dtype ) )
        logger.debug( "choices %s, len(choices): %s, dtype: %s" % (choices, len(choices), choices.dtype) )
        logger.debug( "beta_estimate: %s, dtype: %s" % (beta_estimate, beta_estimate.dtype) )

        return logistic_regression(log_ratios, choices, beta_estimate)
        


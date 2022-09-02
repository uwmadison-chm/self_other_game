#!/usr/bin/env python
import sys
from offers.models import *
import random
import math
import numpy

from django.conf import settings


def main(s_count = 1, trials_per_bin=50, sigma=1.0, min_offer=1, max_offer=1000, debug_out = sys.stderr):

    print("Running %s test subjects with %s trials per bin" % (s_count, trials_per_bin))
    print("sigma = %s, minimum offer = %s, max offer = %s" % (sigma, min_offer, max_offer))
    
    session = Session.objects.get(session_number=999)
    session.distribution_sigma = sigma
    session.minimum_offer = min_offer
    session.maximum_offer = max_offer
    session.save()
    ScheduledPairing.objects.filter(session=session).delete()
    for s in session.subject_set.all():
        s.choice_set.all().delete()
        s.delete()
    
    for p in Pairing.objects.all():
        ScheduledPairing.objects.create(
            pairing=p,
            session=session,
            choice_count=trials_per_bin,
            probing_count=0
        )
    
    for x in range(s_count):
        subj = Subject.objects.create(subject_number=x, session=session)
        ratios = {}
        for p in Pairing.objects.all():
            # Allow ratios up to about 50:1
            ratios[str(p)] = random.uniform(-4.0, 4.0)
        choice = subj.next_choice()
        
        while choice is not None:
            offer_ratio = numpy.log(choice.ratio())
            my_ratio = ratios[str(choice.pairing)]
            logit=(1/(1+numpy.exp(my_ratio-offer_ratio)))
            choice.chose_self = (numpy.random.random() <= logit)
            choice.save()
            # print >> debug_out, ("Choice: %s : ratio %s, desired %s, chose_self : %s" % (choice, log_ratio, desired_ratio, choice.chose_self))
            print >> sys.stderr, "subject %s:\tmy_ratio: %s\toffer_ratio: %s\tchose_self: %s" % (subj.subject_number, my_ratio, offer_ratio, choice.chose_self)
            choice = subj.next_choice()
        
        ld = LogisticOfferDispenser()
        
        for p in Pairing.objects.all():
            data = ld.regress(
                subj.log_ratios_numpy(p),
                subj.choices_numpy(p)
            )
            ip = ld.indifference_point(data[0][0], data[0][1])
            try:
                lip = math.log(ip)
            except:
                lip = 0
            print >> debug_out, ("%s\t%s\t%s\t%s" % (subj.subject_number, p, ratios[str(p)], lip))
        

def multimain(start, stop, step):
    for trial_count in range(start, stop, step):
        try:
            f = open(("%s.txt" % trial_count), "w")
            main(trials_per_bin=trial_count, s_count=100, debug_out=f)
            f.close()
        except:
            print "Fuck"
        
if __name__ == "__main__":
    main()
import random
from offers.models import LogisticOfferDispenser

class SubjectTester(object):
    """docstring for TestSubject"""
    def __init__(self, subject, desired_ratio = 1.0, error_rate = 0.0,
        dispenser = LogisticOfferDispenser()):
        self.subject = subject
        self.error_rate = error_rate
        self.desired_ratio = desired_ratio
        self.dispenser = dispenser
    
    def play_turn(self, choice):
        ratio = float(choice.other_offer)/choice.self_offer
        choose_self = (ratio >= self.desired_ratio)
        #error_flip = random.random() < self.error_rate
        error_flip = self.flip(ratio)
        # When error_flip is true, flip choose_self
        choose_self = choose_self ^ error_flip
        return choose_self, ratio, self.desired_ratio, error_flip
    
    
    def flip(self, ratio):
        pd = abs((self.desired_ratio - ratio)/self.desired_ratio)
        # Use an inverse polynomial function to model something that decays
        # from .5 to Something Small very quickly
        #prob_flip = (1/(3*pd+1)**3)/2
        #print (pd, prob_flip)
        prob_flip = self.error_rate
        return (random.random() < prob_flip)
    
    def play_turns(self):
        #self.subject.choice_set.all().delete()
        c = self.subject.next_choice()
        i = 0
        while c is not None:
            pd = self.dispenser.offer_data(self.subject)
            c.self_offer = pd['offers'][0]
            c.other_offer = pd['offers'][1]
            self.subject.alpha_estimate = pd['regdata'][0][0]
            self.subject.beta_estimate = pd['regdata'][0][1]
            self.subject.save()
            result, ratio, desired_ratio, was_error = self.play_turn(c)
            print("round %3s : %.3f\t%.3f\t%.3f\t%s\t%5s\t%5s" % (i, desired_ratio, self.subject.indifference_estimate(), ratio, (c.self_offer, c.other_offer), result, was_error))
            c.chose_self = result
            c.save()
            i = i + 1
            c = self.subject.next_choice()
    
    
            
    def do_probes(self):
        p = self.subject.next_probe()
        while p is not None:
            p.completed = True
            p.save()
            p = self.subject.next_probe()


def print_summary(subject):
    i = 0
    choices = subject.choice_set.all().order_by('id')
    for c in choices:
        i = i+1
        print "round %3s :\t%.3f\t%s" % (i, c.ratio(), c.chose_self)
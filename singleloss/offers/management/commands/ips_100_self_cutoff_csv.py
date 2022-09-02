from django.core.management.base import BaseCommand
from offers import models
import csv

from offers.logreg import logistic_regression
import numpy
from scipy.linalg import LinAlgError
from scipy.linalg import inv


class Command(BaseCommand):
    help = 'ips_100_self_cutoff CSV'

    def handle(self, *args, **kwargs):
        writer = csv.writer(self.stdout)
        header_columns = ['subject_number', 'alpha_estimate', 'beta_estimate', 'indifference_point', 'alpha_SE', 'beta_SE', 'AIC', 'used_choices']
        writer.writerow(header_columns)
        subjects = [s for s in models.Subject.objects.all() if s.finished()]
        for s in subjects:
            offers_np = s.offers_numpy()
            self_offer_big = (offers_np[:,0] >= 100)
            big_count = numpy.sum(self_offer_big)
            choices_np = s.choices_numpy()
            lr_np = s.log_ratios_numpy()
            try:
                result = logistic_regression(lr_np[self_offer_big], choices_np[self_offer_big])
                betas = result[0]
                cov = inv(result[1])
                std_err = cov.diagonal()**0.5 # Square root of diagonal!
                aic = 2*len(result[0])-2*result[2]
            except LinAlgError:
                result = 'Singular matrix'
                betas = [5,.0001]
                std_err = [0,0]
                aic = 1

            if numpy.isnan(aic):
                aic = 1
            
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

            writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1], aic, big_count])

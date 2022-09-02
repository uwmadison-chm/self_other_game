from django.core.management.base import BaseCommand
from offers import models
import csv

from offers.logreg import logistic_regression
import numpy
from scipy.linalg import LinAlgError
from scipy.linalg import inv 


class Command(BaseCommand):
    help = 'dump IPs as csv'

    def handle(self, *args, **kwargs):
        writer = csv.writer(self.stdout)
        header_columns = ['subject_number', 'alpha_estimate', 'beta_estimate', 'indifference_point', 'alpha_SE', 'beta_SE', 'AIC']
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

                if( sum(choices_np) > (.9*len(choices_np)) ):
                    ip = 3 
                if( sum(choices_np) < (.1*len(choices_np)) ):
                    ip = -3; 

                if( ip > 3 ):
                    ip = 3
                elif( ip < -3 ):
                    ip = -3

                writer.writerow([s.session_and_subject, betas[0], betas[1], ip, std_err[0], std_err[1], aic])

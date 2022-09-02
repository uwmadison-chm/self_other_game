from django.core.management.base import BaseCommand
from offers import models
import csv
from offers.logreg import logistic_regression
import numpy
from scipy.linalg import LinAlgError
from scipy.linalg import inv
import math

class Command(BaseCommand):
    help = 'Dump summary CSV'

    def handle(self, *args, **kwargs):

        ip_thingies = [20, 50, 100, 200]

        writer = csv.writer(self.stdout)
        header_columns = ['subject_number'] + ['ip_%s' % c for c in ip_thingies]
        writer.writerow(header_columns)
        subjects = [s for s in models.Subject.objects.all() if s.finished()]
        for s in subjects:
            choices_np = s.choices_numpy()
            lr_np = s.log_ratios_numpy()
            ip_for_counts = []
            for count in ip_thingies:
                try:
                    result = logistic_regression(lr_np[0:count], choices_np[0:count])
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
                ip_for_counts.append(ip)
            row = [s.session_and_subject] + list(ip_for_counts)
            writer.writerow(row)

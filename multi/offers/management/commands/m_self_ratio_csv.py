from django.core.management.base import BaseCommand
from offers import models
import csv

from offers.logreg import logistic_regression
import numpy
from scipy.linalg import LinAlgError
from scipy.linalg import inv


class Command(BaseCommand):
    help = 'm_self_ratio CSV'

    def handle(self, *args, **kwargs):
        writer = csv.writer(self.stdout)
        header_columns = ['subject_number', 'alpha', 'beta_self', 'beta_ratio', 'alpha_SE', 'beta_self_SE', 'beta_ratio_SE', 'AIC']
        writer.writerow(header_columns)
        subjects = models.Subject.objects.all()
        for s in subjects:
            if s.finished():
                offers_np = s.offers_numpy()
                choices_np = s.choices_numpy()
                lr_np = s.log_ratios_numpy()
                self_ratio = numpy.vstack([offers_np[:,0], lr_np])
                try:
                    result = logistic_regression(self_ratio, choices_np.T)
                    betas = result[0]
                    cov = inv(result[1])
                    std_err = cov.diagonal()**0.5 # Square root of diagonal!
                    aic = 2*len(result[0])-2*result[2]
                except LinAlgError:
                    result = 'Singular matrix'
                    betas = [5,.0001,.0001]
                    std_err = [0,0,0]
                    aic = 1

                if numpy.isnan(aic):
                    aic = 1

                # Can't compute indifference point in this case; it'd just
                # be a function
                writer.writerow([s.session_and_subject, betas[0], betas[1], betas[2], std_err[0], std_err[1], std_err[2], aic])

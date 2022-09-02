"""
 Python module for computing Logistic Regression.
 Requires numpy (http://numpy.scipy.org)

 Version: 20060629

 Contact:  Jeffrey Whitaker <jeffrey.s.whitaker@noaa.gov>

 copyright (c) by Jeffrey Whitaker.
 
 Permission to use, copy, modify, and distribute this software and its
 documentation for any purpose and without fee is hereby granted,
 provided that the above copyright notice appear in all copies and that
 both the copyright notice and this permission notice appear in
 supporting documentation.
 THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
 INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO
 EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
 CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
 USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
 OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
 PERFORMANCE OF THIS SOFTWARE.

"""

import numpy as NP
import scipy
from scipy import linalg

def simple_logistic_regression(x,y,beta_start=None,verbose=False,
                               CONV_THRESH=1.e-3,MAXIT=500):
    """
 Uses the Newton-Raphson algorithm to calculate maximum
 likliehood estimates of a simple logistic regression.  

 Faster than logistic_regression when there is only one predictor.

 x - predictor
 y - binary outcomes (len(y) = len(x))
 beta_start - initial beta (default zero)
 if verbose=True, diagnostics printed for each iteration.
 MAXIT - max number of iterations (default 500)
 CONV_THRESH - convergence threshold (sum of absolute differences
  of beta-beta_old)

 returns beta (the logistic regression coefficients, a 2-element vector),
 J_bar (the 2x2 information matrix), and l (the log-likeliehood).
 J_bar can be used to estimate the covariance matrix and the standard
 error beta.
 l can be used for a chi-squared significance test.

 covmat = inverse(J_bar)     --> covariance matrix
 stderr = sqrt(diag(covmat)) --> standard errors for beta
 deviance = -2l              --> scaled deviance statistic
 chi-squared value for -2l is the model chi-squared test.
    """
    if len(x) != len(y):
        raise ValueError, "x and y should be the same length!"
    if beta_start is None:
        beta_start = NP.zeros(2,x.dtype)
    iter = 0; diff = 1.; beta = beta_start  # initial values
    if verbose:
        print 'iteration  beta log-likliehood |beta-beta_old|' 
    while iter < MAXIT:
        beta_old = beta 
        p = 1./(1.+NP.exp(-(beta[0]+beta[1]*x)))
        #p = NP.exp(beta[0]+beta[1]*x)/(1.+NP.exp(beta[0]+beta[1]*x))
        #p = 1.0/(1+(x/beta[0])**(-beta[1])) - .5
        l = NP.sum(y*NP.log(p) + (1.-y)*NP.log(1.-p)) # log-likliehood
        s = NP.array([NP.sum(y-p), NP.sum((y-p)*x)])  # scoring function
        # information matrix
        J_bar = NP.array([[NP.sum(p*(1-p)),NP.sum(p*(1-p)*x)],
                      [NP.sum(p*(1-p)*x),NP.sum(p*(1-p)*x*x)]])
        #print J_bar
        beta = beta_old + NP.dot(linalg.pinv(J_bar),s)  # new value of beta
        # sum of absolute differences
        diff = NP.sum(NP.fabs(beta-beta_old))
        if verbose:
            print iter+1, beta, l, diff
        if diff <= CONV_THRESH: break
        iter = iter + 1
    return beta, J_bar, l

def logistic_regression(x,y,beta_start=None,verbose=False,CONV_THRESH=1.e-3,
                        MAXIT=500):
    """
 Uses the Newton-Raphson algorithm to calculate maximum
 likliehood estimates of a logistic regression.

 Can handle multivariate case (more than one predictor).

 x - rank-2 array of predictors. Number of predictors = x.shape[0]=N
 y - binary outcomes (len(y) = x.shape[1])
 beta_start - initial beta vector (default zeros(N+1,x.dtype)
 if verbose=True, diagnostics printed for each iteration.
 MAXIT - max number of iterations (default 500)
 CONV_THRESH - convergence threshold (sum of absolute differences
  of beta-beta_old)

 returns beta (the logistic regression coefficients, a N+1 element vector),
 J_bar (the (N+1)x(N=1) information matrix), and l (the log-likeliehood).
 J_bar can be used to estimate the covariance matrix and the standard
 error beta.
 l can be used for a chi-squared significance test.

 covmat = inverse(J_bar)     --> covariance matrix
 stderr = sqrt(diag(covmat)) --> standard errors for beta
 deviance = -2l              --> scaled deviance statistic
 chi-squared value for -2l is the model chi-squared test.
    """
    if x.shape[-1] != len(y):
        raise ValueError, "x.shape[-1] and y should be the same length!"
    try:
        N, npreds = x.shape[1], x.shape[0]
    except: # single predictor, use simple logistic regression routine.
        N, npreds = x.shape[-1], 1
        return simple_logistic_regression(x,y,beta_start=beta_start,
               CONV_THRESH=CONV_THRESH,MAXIT=MAXIT,verbose=verbose)
    if beta_start is None:
        beta_start = NP.zeros(npreds+1,x.dtype)
    X = NP.ones((npreds+1,N), x.dtype)
    X[1:, :] = x
    Xt = NP.transpose(X)
    iter = 0; diff = 1.; beta = beta_start  # initial values
    if verbose:
        print 'iteration  beta log-likliehood |beta-beta_old|' 
    while iter < MAXIT:
        beta_old = beta 
        ebx = NP.exp(NP.dot(beta, X))
        p = ebx/(1.+ebx)
        l = NP.sum(y*NP.log(p) + (1.-y)*NP.log(1.-p)) # log-likeliehood
        s = NP.dot(X, y-p)                            # scoring function
        J_bar = NP.dot(X*p,Xt)                        # information matrix
        beta = beta_old + NP.dot(NP.linalg.inv(J_bar),s) # new value of beta
        diff = NP.sum(NP.fabs(beta-beta_old)) # sum of absolute differences
        if verbose:
            print iter+1, beta, l, diff
        if diff <= CONV_THRESH: break
        iter = iter + 1
    if iter == MAXIT and diff > CONV_THRESH: 
        print 'warning: convergence not achieved with threshold of %s in %s iterations' % (CONV_THRESH,MAXIT)
    return beta, J_bar, l

def calcprob(beta, x):
    """
 calculate probabilities (in percent) given beta and x
    """
    try:
        N, npreds = x.shape[1], x.shape[0]
    except: # single predictor, x is a vector, len(beta)=2.
        N, npreds = len(x), 1
    if len(beta) != npreds+1:
        raise ValueError,'sizes of beta and x do not match!'
    if npreds==1: # simple logistic regression
        return 100.*NP.exp(beta[0]+beta[1]*x)/(1.+NP.exp(beta[0]+beta[1]*x))
    X = NP.ones((npreds+1,N), x.dtype)
    X[1:, :] = x
    ebx = NP.exp(NP.dot(beta, X))
    return 100.*ebx/(1.+ebx)

if __name__ == '__main__':
    from numpy.random import multivariate_normal
    # number of realizations.
    nsamps = 100000
    # correlations
    r12 = 0.5 
    r13 = 0.25
    r23 = 0.125 # correlation between predictors.
    # random draws from trivariate normal distribution
    x = multivariate_normal(NP.array([0,0,0]),NP.array([[1,r12,r13],[r12,1,r23],[r13,r23,1]]), nsamps)
    x2 = multivariate_normal(NP.array([0,0,0]),NP.array([[1,r12,r13],[r12,1,r23],[r13,r23,1]]), nsamps)
    print
    print 'correlations (r12,r13,r23) = ',r12,r13,r23
    print 'number of realizations = ',nsamps
    # training data.
    truth = x[:,0]
    climprob = NP.sum((truth > 0).astype('f'))/nsamps
    fcst = NP.transpose(x[:,1:]) # 2 predictors.
    # independent data for verification.
    truth2 = x2[:,0]
    fcst2 = NP.transpose(x2[:,1:])
    # compute logistic regression.
    obs_binary = truth > 0.
    # using only 1st predictor.
    beta,Jbar,llik = logistic_regression(fcst[0,:],obs_binary,verbose=True)
    covmat = NP.linalg.inv(Jbar)
    stderr = NP.sqrt(NP.diag(covmat))
    print 'using only first predictor:'
    print 'beta =' ,beta
    print 'standard error =',stderr
    # forecasts from independent data.
    prob = calcprob(beta, fcst2[0,:])
    # compute Brier Skill Score
    verif = (truth2 > 0.).astype('f')
    bs = NP.mean((0.01*prob - verif)**2)
    bsclim = NP.mean((climprob - verif)**2)
    bss = 1.-(bs/bsclim)
    print 'Brier Skill Score = ',bss
    # using only 2nd predictor.
    beta,Jbar,llik = logistic_regression(fcst[1,:],obs_binary,verbose=True)
    covmat = NP.linalg.inv(Jbar)
    stderr = NP.sqrt(NP.diag(covmat))
    print 'using only second predictor:'
    print 'beta =' ,beta
    print 'standard error =',stderr
    # forecasts from independent data.
    prob = calcprob(beta, fcst2[1,:])
    # compute Brier Skill Score
    verif = (truth2 > 0.).astype('f')
    bs = NP.mean((0.01*prob - verif)**2)
    bsclim = NP.mean((climprob - verif)**2)
    bss = 1.-(bs/bsclim)
    print 'Brier Skill Score = ',bss
    # using both predictors.
    beta,Jbar,llik = logistic_regression(fcst,obs_binary,verbose=True)
    covmat = NP.linalg.inv(Jbar)
    stderr = NP.sqrt(NP.diag(covmat))
    print 'using both predictors:'
    print 'beta =' ,beta
    print 'standard error =',stderr
    # forecasts from independent data.
    prob = calcprob(beta, fcst2)
    # compute Brier Skill Score
    verif = (truth2 > 0.).astype('f')
    bs = NP.mean((0.01*prob - verif)**2)
    bsclim = NP.mean((climprob - verif)**2)
    bss = 1.-(bs/bsclim)
    print 'Brier Skill Score = ',bss
    print """

If Brier Skill Scores are within +/- 0.01 of 0.16, 0.04 and 0.18 everything is OK"""

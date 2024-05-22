#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Homemade fitting module
"""

import scipy as sp
import numpy as np
pi=np.pi
from scipy.special import erf
from scipy import optimize
import time

class FitUtility():
    """Class to fit function to data."""
    
    def __init__(self, x, y, fitFunction, yerr=None, p_in = None, p_fix=None, NumberOfSteps=None, printbool=False):
        """Initialize class instance and fit function to data
        	
        
        Args:
            x (list or np.array or None) : x vector of data to fit. If None, then x=np.arange(len(y)).
            
            y (list or np.array) : y vector of data to fit.
            
            fitFunction (FitFunction) : the function to fit to data.
        
        Keyword Args: 
            yerr (list or np.array or None) : the error in the y vector.
            
            p_in (list or None) : initial fit parameters.
            
            p_fix (list or None) : array of strings or values.
            
            NumberOfSteps (int or None) : number how many y-fitted points will generated for plotting arrays xfit and yfit.
                If None, NumberOfSteps = len(y).
                
            printbool (bool) : if the parameters info of the fit should be printed.
        """
         
        starttime = time.time()
        
        if p_in is None or len(p_in)!= len(fitFunction.p) :
            fitFunction.p = [None] * len(fitFunction.p)
        else :
            fitFunction.p = p_in
         
        if x is None:
            x_array = np.arange(len(y))
        else:
            x_array = sp.array(x)
        y_array = sp.array(y)
        yerr_array = sp.array(yerr)
        
        # Check if y is 2D if yes make 1D array ...
        try:
            len(y[0])
            y_array = []
            x_array = [ [], [] ]
            for i,val in enumerate(y):
                y_array.append(val)
                if x is None:
                    x_array[0].append(np.zeros(len(val)+i))
                    x_array[1].append(np.arrange(len(val)))
            x_array = sp.array(x_array)
            y_array = sp.array(y_array)
        except:
            None
        
        # create p_fix full of None if there is None
        if p_fix is None:
            p_fix = [None] * len(fitFunction.p)
    
        # to be robust add Nones to p_fix array if it shorter than fitFunction.p
        pdiff = len(fitFunction.p)-len(p_fix)
        if pdiff > 0:
            p_fix = p_fix + [None]*pdiff
    	
        # function to show init value if requested
        def printif(string, pindex):
            if printbool:
                try:
                    print(fitFunction.pdetail[pindex] + ': ' + string)
                except:
                    print('For p' + str(pindex) + ': ' + string)
    
        # create empty p0
        pinits = [None] * len(fitFunction.p)
        # fill pinits if there is None in fitFunction.p with the getinits function
        for i,val in enumerate(fitFunction.p):
            try: 
                pinits[i] = fitFunction.getinits(x_array, y_array)[i]
                printif('Auto detected initial parameter: ' + str(pinits[i]), i)
            except:
                if fitFunction.p[i] == None:
                    pinits[i] = 1
                    printif('ser initial parameter value to 1', i)
                else:
                    pinits[i] = fitFunction.p[i]
                    printif('Got initial parameter value from setted array', i)
                   
        p0 = []
        for i,val in enumerate(p_fix):
            if val == None:
                p0.append(pinits[i])
            if type(val) == str:
                try:
                    startpar = val.find('par[')
                    endpar = val[startpar+4:].find(']')
                    if int(val[startpar+4: startpar+4+endpar])==i:
                        p0.append(pinits[i])
                except:
                    None
        
        # Define (weight)errfunc depending p_fix
        def errfunc(par, xf, yf):
            # create parameters p for fit depending of p_fix
            p = []
            ii = 0
            for i,val in enumerate(p_fix):
                try:
                    if val == None:
                        p.append(par[ii])
                        ii += 1
                    else:
                        if type(val) == str:
                            p.append(eval(val))
                        else:
                            p.append(val)
                except:
                    p.append(pinits[i])
        
            return yf - fitFunction.execute(p,xf)
    
        # just use errfunc to make weighterrrfunc...
        def weighterrfunc(par, xf, yf, yerrf):
            return errfunc(par, xf, yf) / yerrf
        
        # Check if there are y errors
        if not(yerr is None) and not(np.any(yerr_array == 0)) :
            p1, pcovmat, infodict, mesg, ier = optimize.leastsq(weighterrfunc, p0, args=(x_array, y_array, yerr_array), full_output=True)
        else:
            p1, pcovmat, infodict, mesg, ier = optimize.leastsq(errfunc, p0, args=(x_array, y_array), full_output=True)
            
        # Calculate fit results
        try: 
            len(y[0])
            x_fit = x_array
        except:
            if NumberOfSteps == None:
                x_fit = x_array
            else:
                x_fit = np.linspace(min(x_array), max(x_array), NumberOfSteps)
            
        # prepare p1 for execute use
        pfit = []
        ii = 0
        for i,val in enumerate(p_fix):
            if val == None:
                pfit.append(p1[ii])
                ii += 1
            else:
                if type(val) == str:
                    pfit.append(eval(val))
                else:
                    pfit.append(val)
        y_fit = fitFunction.execute(pfit, x_fit)
        
        #calculate parameters errors from covariance matrix if yerr provided and fit works
        if not(yerr is None) and not(np.any(yerr_array == 0)) and (0< ier <5) and not(pcovmat is None):
            # dof = float(len(y_array) - len(p1))
            # if dof<1 : dof=1
            # pcovmat *= len(y_array)/dof
            self.psigma = np.sqrt(np.abs(np.diag(pcovmat)))
        else :
            self.psigma = None
    
        # add results to class
        self.fitFunction_detail = fitFunction.detail
        try:
            self.pdetail = fitFunction.pdetail
        except:
            None
        self.fitFunction = lambda xex : fitFunction.execute(pfit,xex)
        self.fitFunction_name = fitFunction.name
        self.x = x_fit
        self.y = y_fit
        self.pfit = pfit
        self.p = pfit
        self.pinit = pinits
        self.pcovmat = pcovmat
        self.infodict = infodict
        self.mesg = mesg
        self.ierror = ier
        
        if not(0< ier <5) :
            self.p = [0.]*len(fitFunction.p)
            print("Warning : Fit of "+self.fitFunction_name+" function did not converge : set fit.p to 0. array")
            # print("error message from optimize.leastsq :")
            # print(mesg)
        
        #check the quality of the fit
#        y_normalized= y_array/float( np.sqrt( sum( [y_array[i]**2    for i in range(len(y_array))]    )) )
#        y_fit = fitFunction.execute(pfit, x_array)
#        y_fit_normalized = y_fit/ float( np.sqrt( sum( [y_fit[i]**2    for i in range(len(y_fit))] )))
#        self.quality = sum(y_fit_normalized*y_normalized)        
        self.fitduration = time.time()-starttime
            
           
        #return self.quality, fitduration
	      




####################################################################################
# list of fit functions for web server (is shown when a parameter called 
# "fitFunction" is present in the "do" method of the module)
fitFunctionsList = []


####################################################################################
# definitions of function to be used for fitting.


class FitFunction:
    """Class of function for use in FitUtility"""
    
    name = ""
    detail = ""
    p = None
    
    def __init__(self):
        return None
    
    def execute(self, p, x):
        """Function execution.
        
        Args: 
            p (list(float)) : function parameters.
            
            x (float) : function variable.
            
        Return:
            y (float) : function value.
        """
        return 0.

    def getinits(self, x, y):
        """Automatic initialization of function parameters.
        
        Args: 
            x (list or np.array) : x vector of data to fit. 
            
            y (list or np.array) : y vector of data to fit.
            
        Return:
            pinits (list(float)) : function parameters.
        """
        return [0.]
    


#linear fit 
linear = FitFunction()
linear.name = "Linear"
linear.detail = "SlopeP0  * x + OffsetP1"
linear.p = [None] * 2
linear.pdetail = ['Slope', 'Offset']
def getinits(x, y):
    return [ (y.max()-y.min())/(x.max()-y.min()), y.min() ]
linear.getinits = getinits
def execute(p, x):
	return p[0] * x + p[1]
linear.execute = execute
fitFunctionsList.append(linear)


#Adding sin fit to the fit list
sinus = FitFunction()
sinus.name = "Sinus"
sinus.detail = "AmplitudeP0 * sin(x / FrequencyP1 + xTranslationPhaseP2) + OffsetP3"
sinus.p = [None] * 4
def getinits(x,y):
    return [ (y.max()-y.min())/2., 0, abs(x.man()-y.min()), (y.max()+y.min())/2. ]
sinus.getinits = getinits
sinus.pdetail = [ 'Amplitude', 'xTranslation', 'Frequency', 'Offset']
def execute(p, x):
	return p[0] * np.sin(pi * x / p[1] + p[2]) + p[3]
sinus.execute = execute
fitFunctionsList.append(sinus)


#Adding exp + decay fit to the fit list
expdecay= FitFunction()
expdecay.name = "Exponential decay"
expdecay.detail = "AmplitudeP0 * exp( - x / DecaytimeP2) + OffsetP3"
expdecay.p = [None] * 3
expdecay.pdetail = [ 'Amplitude', 'Decaytime', 'Offset']
def getinits(x, y):
    return [ y.max()-y.min() , (x.max()-x.min())/2., y.min() ]
expdecay.getinits = getinits
def execute(p, x):
	return p[0] * np.exp(-x/p[1]) + p[2]
expdecay.execute = execute
fitFunctionsList.append(expdecay)


#Rabi frequency fit
sinusdecay = FitFunction()
sinusdecay.name = "Sinus exponential decay"
sinusdecay.detail = "AmplitudeP0 * np.exp(- (x-xTranslationP1) / DecaytimeP2) * np.sin((x-xTranslationP1)/ FrequencyPp3) + OffsetP4"
sinusdecay.p = [None] * 5
sinusdecay.pdetail = [ 'Amplitude', 'xTranslation', 'Decaytime', 'Frequency', 'Offset']
def getinits(x, y):
    return [ y.max(), 0. , x.max()-x.min(), (x.max()-x.min())/3, y.min() ]
def execute(p, x):
	return p[0] * np.exp(- (x-p[1]) / p[2]) * np.sin((x-p[1])/ p[3]) + p[4]
sinusdecay.execute = execute
fitFunctionsList.append(sinusdecay)


#Adding gauss fit
gauss = FitFunction()
gauss.name = "Gaussian"
gauss.detail = "AmplitudeP0 * exp(-(x-xTranslationP1)**2 / (2 *sigmaP2**2)) + OffsetP3"
gauss.p = [None] * 4
gauss.pdetail = [ 'Amplitude', 'xTranslation', 'sigma', 'Offset' ]
def getinits(x, y):
    imin = int(len(y)/10.)
    imax = len(y)-int(len(y)/10.)
    y = y[imin:imax-1]
    x = x[imin:imax-1]
    return [ y.max()-y.min(), np.extract(y>((y.max()-y.min())*2./3.+y.min()),x).mean(),
            np.extract(y>((y.max()-y.min())*2./3.+y.min()),x).std(), y.min()]
gauss.getinits = getinits
def execute(p, x):
    return p[0] * np.exp(-(x - p[1]) ** 2 / (2* (p[2]**2))) + p[3]
gauss.execute = execute
fitFunctionsList.append(gauss)

#Adding gauss fit with positive amplitude
gaussabs = FitFunction()
gaussabs.name = "Gaussian"
gaussabs.detail = "AmplitudeP0**2 * exp(-(x-xTranslationP1)**2 / (2 *sigmaP2**2)) + OffsetP3"
gaussabs.p = [None] * 4
gaussabs.pdetail = [ 'AmplitudeAbs', 'xTranslation', 'sigma', 'Offset' ]
def getinits(x, y):
    imin = int(len(y)/10.)
    imax = len(y)-int(len(y)/10.)
    y = y[imin:imax-1]
    x = x[imin:imax-1]
    return [ np.sqrt(y.max()-y.min()), np.extract(y>((y.max()-y.min())*2./3.+y.min()),x).mean(),
            np.extract(y>((y.max()-y.min())*2./3.+y.min()),x).std(), y.min()]
gaussabs.getinits = getinits
def execute(p, x):
    return p[0]**2 * np.exp(-(x - p[1]) ** 2 / (2* (p[2]**2))) + p[3]
gaussabs.execute = execute
fitFunctionsList.append(gaussabs)


#Adding lorentz fit
lorentz = FitFunction()
lorentz.name = "Lorentzian"
lorentz.detail = "AmplitudeP0 * FHWMP1/2 / pi /( (FHWMP1/2)^2 * (x-xTranslationP1)^2) + OffsetP3"
lorentz.p = [None] * 4
lorentz.pdetail = ['Amplitude', 'xTranslation', 'FWHM', 'Offset']
def getinits(x, y):
    return [ y.max(), (x.max()+x.min())/2, abs((x.max()-x.min())/10), y.min() ]
lorentz.getinits = getinits
def execute(p, x):
    return p[0] * (p[2]/2)/pi / ( (p[2]/2)**2 + (x - p[1]) ** 2 ) + p[3]
lorentz.execute = execute
fitFunctionsList.append(lorentz)


# Adding error function (integrated gauss profile)
error_function = FitFunction()
error_function.name = "Error Function"
error_function.detail = "AmplitudeP0 * erf( np.sqrt(2) * (x-xTranslationP1) / WaistP2) + OffsetP3"
error_function.p = [None] * 4
error_function.pdetail = ['Amplitude', 'xTranslation', 'Waist', 'Offset']
def getinits(x, y):
    return [ (y[-1]-y[0])/2, (x[-1]+x[0])/2., (x[-1]-x[0])/5., -y.min()+(y[-1]-y[0])/2 ]
error_function.getinits = getinits
def execute(p, x):
	return p[0] * erf(np.sqrt(2)*(x-p[1])/p[2]) + p[3]
error_function.execute = execute
fitFunctionsList.append(error_function)


# Adding spot size function
spotsize = FitFunction()
spotsize.name = "Spot Size Funtionc versus z-Position"
spotsize.detail = " WaistP0 sqrt( 1 + ((x-xTranslationP1)*WavelengthP2*MsquareP3 / (np.pi*WaistP0**2)**2) )"
spotsize.p = [None] * 4
spotsize.pdetail = ['Waist', 'xTranslation', 'Wavelength', 'Msquare']
def getinits(x, y):
    return [ y.min(), (x[-1]+x[0])/2., 1e-4, 1 ]
spotsize.getinits = getinits
def execute(p, x):
	return p[0] * np.sqrt( 1 + ((x-p[1])*p[2]*p[3] / (np.pi*p[0]**2))**2)
spotsize.execute = execute
fitFunctionsList.append(spotsize)


# Adding Ellipse
ellipse = FitFunction()
ellipse.name = "Upper part of a rotated Ellipse"
ellipse.detail = "-B + sqrt(B**2 - 4*A*C) / (2*A) + OffsetP4"
ellipse.p = [None] * 5
ellipse.pdetail = ['SemiAxisa', 'SemiAxisb', 'RotationAngle', 'xTranslation', 'Offset']
def getinits(x, y):
    return [ (x[-1]-x[0])/2. , (y[-1]-y[0])/2. , 0 , (x[-1]+x[0])/2. , y.min()+(y[-1]-y[0])/2. ]
ellipse.getinits = getinits
def execute(p, x):
    x = x-p[3]
    theta = p[2]*180.0/np.pi
    A = p[1]**2 * (np.sin(theta))**2 + p[0]**2 * (np.cos(theta))**2
    B = (p[1]**2 - p[0]**2) * np.sin(2*theta) * x
    C = p[1]**2 * (np.cos(theta))**2 * x**2  +  p[0]**2 * (np.sin(theta))**2 * x**2  -  p[0]**2 * p[1]**2
    root = B**2-4*A*C
    for i,val in enumerate(root):
        if val < 0:
            root[i] = 1e20
    return ( -B + np.sqrt(root) ) / (2*A) + p[4]
ellipse.execute = execute
fitFunctionsList.append(ellipse)


# Adding Radius of ellipse vs angle
ellipse_radius = FitFunction()
ellipse_radius.name = "Radius of ellipse versus Angle"
ellipse_radius.detail = "SemiAxisbP0 / sqrt( 1 - EccentricityP1**2 * (cos(x-xTranslation)**2)"
ellipse_radius.p = [None] * 3
ellipse_radius.pdetail = ['SemiAxisb', 'Eccentricity', 'xTranslation']
def getinits(x, y):
    return [ y.min(), y.min()/y.max(), x[y.argmax()] ]
ellipse_radius.getinits = getinits
def execute(p,x):
    return p[0] / np.sqrt(1-p[1]**2*(np.cos((x-p[2])*np.pi/180.))**2)
ellipse_radius.execute = execute
fitFunctionsList.append(ellipse_radius)



#################################### old 2D fits for being compatible #######


#linear fit 
lin_fit = FitFunction()
lin_fit.name = "Linear"
lin_fit.detail = "SlopeP0  * x + OffsetP1"
lin_fit.p = [None] * 2
lin_fit.pdetail = ['Slope', 'Offset']
def getinits(x, y):
    return [ (y.max()-y.min())/(x.max()-y.min()), y.min() ]
lin_fit.getinits = getinits
def execute(p, x):
	return p[0] * x + p[1]
lin_fit.execute = execute
fitFunctionsList.append(lin_fit)


#Adding sin fit to the fit list
sinfit = FitFunction()
sinfit.name = "Sinus fit"
sinfit.detail = "AmplitudeP0 * sin(x / FrequencyP1 + PhaseP2)"
sinfit.p = [None] * 3
def getinits(x,y):
    return [ (y.max()-y.min())/2., abs(x.man()-y.min()), 0 ]
sinfit.getinits = getinits
sinfit.pdetail = [ 'Amplitude', 'Frequency', 'Phase']
def execute(p, x):
	return p[0] * np.sin(pi * x / p[1] + p[2])
sinfit.execute = execute
fitFunctionsList.append(sinfit)


#Adding cos fit to the fit list
cosfit_with_phase = FitFunction()
cosfit_with_phase.name = "cos with offset and phase"
cosfit_with_phase.detail = " -p[0] * cos(2 * x * pi + p[2] ) + p[1]"
cosfit_with_phase.p = [2., 0, 0]
def execute(p, x):
	return -p[0] * np.cos(2 * x * pi + p[2]) + p[1]  #factor two in phase for parity of two ions
cosfit_with_phase.execute = execute
fitFunctionsList.append(cosfit_with_phase)

#Adding cos fit to the fit list
cosfit = FitFunction()
cosfit.name = "cos with offset"
cosfit.detail = "-p[0] * cos(2 * x * pi) + p[1]"
cosfit.p = [2., 0]
def execute(p, x):
	return -p[0] * np.cos(2 * x * pi) + p[1]  #factor two in phase for parity of two ions
cosfit.execute = execute
fitFunctionsList.append(cosfit)

#Adding cos fit to the fit list
ramsey_fit = FitFunction()
ramsey_fit.name = 	"fit for ramsey experiment"
ramsey_fit.detail =	"1/2 [ 1-  p[0] cos( x * pi + p[1]) ] "
ramsey_fit.p = [1., 0]
def execute(p, x):
	return   1./2 * ( 1.0 - p[0]*np.cos(x*pi + p[1]) ) 
ramsey_fit.execute = execute
fitFunctionsList.append(ramsey_fit)


#Adding exp + decay fit to the fit list
exp_decay_plus_offset = FitFunction()
exp_decay_plus_offset.name = "exp decay + off"
exp_decay_plus_offset.detail = "p[0] * exp(-x / p[1]) + p[2]"
exp_decay_plus_offset.p = [.3, 4, .5]
def execute(p, x):
	return p[0] * np.exp(-x / p[1]) + p[2]
exp_decay_plus_offset.execute = execute
fitFunctionsList.append(exp_decay_plus_offset)


#Rabi frequency fit
rabi_freq_fit = FitFunction()
rabi_freq_fit.name ="Rabi Freq Fit"
rabi_freq_fit.detail ="1. / 2 * (p[4] + p[0] * np.sin(pi * x / p[2] + p[1]) * np.exp(-x / p[3]) ) "
rabi_freq_fit.p=[1.0, 0, 3, 30, 1]
def execute(p, x):
	return 1. / 2 * (p[4] + p[0] * np.sin(pi * x / p[2] + p[1]) * np.exp(-x / p[3]) )
rabi_freq_fit.execute = execute
fitFunctionsList.append(rabi_freq_fit)

#Adding gauss fit
gauss_background_fit = FitFunction()
gauss_background_fit.name = "Gaussian fit"
gauss_background_fit.detail = "AmplitudeP0 * exp(-(x-xTranslationP1)**2 / (2 *SigmaP2**2)) + OffsetP3"
gauss_background_fit.p = [None] * 4
gauss_background_fit.pdetail = [ 'Amplitude', 'xTranslation', 'Sigma', 'Offset' ]
def getinits(x, y):
    return [ abs(y).max(), x.mean(), (x[-1]-x[0])/3, np.array([ y[0], y[-1] ]).mean()]
gauss_background_fit.getinits = getinits
def execute(p, x):
    return p[0] * np.exp(-(x - p[1]) ** 2 / (2* (p[2]**2))) + p[3]
gauss_background_fit.execute = execute
fitFunctionsList.append(gauss_background_fit)

# Adding triple gauss fit
triple_gauss = FitFunction()
triple_gauss.name = "Triple Gaussian"
triple_gauss.detail = "P0 * exp(-(x - p1) ** 2 / P2) + P3 * exp(-(x - p4) ** 2 / p5) + P6 * exp(-(x - p7) ** 2 / p8))"
triple_gauss.p = [1000, 2, 150,    10, 100, 10,  10 , 200, 50]
def execute(p, x):
	return p[0] * np.exp(-(x - p[1]) ** 2 / p[2])  + p[3] * np.exp(-(x - p[4]) ** 2 / p[5])  + p[6] * np.exp(-(x - p[7]) ** 2 / p[8])
triple_gauss.execute = execute
fitFunctionsList.append(triple_gauss)

#Adding triple Poisson fit
# double Gauss fit:
double_gauss = FitFunction()
double_gauss.name = "double Gaussian"
double_gauss.detail = "P0 * exp(-(x - p1) ** 2 / P2) + P3 * exp(-(x - p4) ** 2 / p5) )"
double_gauss.p = [1000, 2, 150, 10, 50, 10]
def execute(p, x):
	return p[0] * np.exp(-(x - p[1]) ** 2 / p[2])  + p[3] * np.exp(-(x - p[4]) ** 2 / p[5])
double_gauss.execute = execute
fitFunctionsList.append(double_gauss)

# # triple Poisson fit
# triple_poisson = FitFunction()
# triple_poisson.name="TriplePoisson"
# triple_poisson.detail = ""
# triple_poisson.p= [  1, 100, 200, .25, .5 , .25]
# def execute(p, x):
# 	bin_size=(x[1]-x[0])
# 	poisson1=poisson.PoissonCalculator().poisson(x,float(p[0]) ) 
# 	poisson1=poisson1/float(sum(poisson1))*p[3]
# 	poisson2=poisson.PoissonCalculator().poisson(x,float(p[1]))
# 	poisson2=poisson2/float(sum(poisson2)) * p[4]
# 	poisson3=poisson.PoissonCalculator().poisson(x,float(p[2]))
# 	poisson3=poisson3/float(sum(poisson3)) * p[5]
# 	poisson_complete =[ poisson1[i] + poisson2[i] + poisson3[i]  for i in range(len(x))] 
# 	poisson_complete =poisson_complete/bin_size
# 	return poisson_complete
# triple_poisson.execute = execute
# fitFunctionsList.append(triple_poisson)

# # double Poisson fit
# double_poisson = FitFunction()
# double_poisson.name = "double Poissonian"
# double_poisson.detail = ""
# double_poisson.p = [1, 50, .25, .5]
# def execute(p, x):
# 	bin_size = (x[1] - x[0])
# 	poisson1 = poisson.PoissonCalculator().poisson(x, float(p[0]) ) 
# 	poisson1 = poisson1 / float(sum(poisson1)) * p[2]
# 	poisson2 = poisson.PoissonCalculator().poisson(x, float(p[1]))
# 	poisson2 = poisson2 / float(sum(poisson2)) * p[3]
# 	poisson_complete = [poisson1[i] + poisson2[i] for i in range(len(x))] 
# 	poisson_complete = poisson_complete/bin_size
# 	return poisson_complete
# double_poisson.execute = execute
# fitFunctionsList.append(double_poisson)

#Adding triple lorentzian fit
triple_lorentz = FitFunction()
triple_lorentz.name = "Triple Lorentzian"
triple_lorentz.detail = "Sum^3_i=1 = A_i p_i / (pi p_i^2 + pi * (x-x_0i)^2) + p_0"
# Default values of initial Parameters:
# three lorentz i=[0,1,2]
# p[0,3,6] = amplitude of each lorentz
# p[1,4,7] = each gamma ( FHWM/2 )
# p[2,5,8] = each shift in time
# p[9] = common offset (Background)
triple_lorentz.p = [1000, 2, 150, 10, 100, 10,  10 , 200, 50, 1]
def execute(p, x):
	return p[0] * p[1] /( pi* p[1]**2 + pi*(x - p[2]) ** 2 ) +p[3] * p[4] /( pi* p[4]**2 + pi*(x - p[5]) ** 2 )  +p[6] * p[7] /( pi* p[7]**2 + pi*(x - p[8]) ** 2 ) + p[9]
triple_lorentz.execute = execute
fitFunctionsList.append(triple_lorentz)




#################################### 3D - function ###########################

## adding Ellipsoid
ellipsoid = FitFunction()
ellipsoid.name = "3D ellipsoid fit the lower part"
ellipsoid.detail = "ellipsoid fit with three main axis and shifted origin"
ellipsoid.p_fix = [None] * 7
ellipsoid.pdetail = ['SemiAxisz','SemiAxisa','SemiAxisb','RotationAngle','xTranslation','yTranslation','Offset']
def getinits(x, z):
    return [ z.max() ,x[0][-1]-x[0][0], x[0][-1]-x[0][0], 0., 0., 0., z.max() ]
ellipsoid.getinits = getinits
def execute(p,x):
    xn, yn = rotation(x[0],x[1], p[3])
    xn = xn - p[4]
    yn = yn - p[5]
    root = 1. - xn**2/p[1]**2 - yn**2/p[2]**2
    for i,val in enumerate(root):
        if val < 0:
            root[i] = 1000000000.
    return -p[0]*np.sqrt( root ) + p[6]
ellipsoid.execute = execute
fitFunctionsList.append(ellipsoid)

## adding gauss 2D
gauss2D = FitFunction()
gauss2D.name = "3D gauss fit"
gauss2D.detail = "3D gauss fit with two rotatable axes and shifted origin"
gauss2D.p_fix = [None] * 7
gauss2D.pdetail = ['Amplitude','Sigmaa','Sigmab','RotationAngle','xTranslation','yTranslation','Offset']
def getinits(x, z):
    return [ z.max() ,x[0][-1]-x[0][0], x[-1][0]-x[0][0], 0., 0., 0., z.max() ]
gauss2D.getinits = getinits
def execute(p,x):
    xn, yn = rotation(x[0],x[1], p[3])
    xn = xn - p[4]
    yn = yn - p[5]
    return p[0] * np.exp( - xn**2/(2*p[1]**2) - yn**2/(2*p[2]**2) ) + p[6]
gauss2D.execute = execute
fitFunctionsList.append(gauss2D)

## adding gauss + linear 2D
gauss_linear2D = FitFunction()
gauss_linear2D.name = "3D gauss + linear fit"
gauss_linear2D.detail = "3D gauss + linear fit with two rotatable waists and shifted origin"
gauss_linear2D.p_fix = [None] * 9
gauss_linear2D.pdetail = ['Amplitude','Sigmaa','Sigmab','RotationAngle','xTranslation','yTranslation','Offset','xSlope','ySlope']
gauss_linear2D.pboundaries = [None, (0.,None), (0.,None), (-180.,180.), None, None, None, None, None]
def getinits(x, z):
    return [ z.max() ,x[0][-1]-x[0][0], x[-1][0]-x[0][0], 0., 0., 0., z.max(), 0.,0.]
gauss_linear2D.getinits = getinits
def execute(p,x):
    xn, yn = rotation(x[0]- p[4], x[1]- p[5], p[3])
    return p[0] * np.exp( - 2*xn**2/(p[1]**2) - 2*yn**2/(p[2]**2) ) + p[6] + p[7]*(x[0]- p[4]) + p[8]*(x[1]- p[5])
gauss_linear2D.execute = execute
fitFunctionsList.append(gauss_linear2D)

##### Help function
def rotation(x,y, theta):
    cos = np.cos(theta*np.pi/180.)
    sin = np.sin(theta*np.pi/180.)
    xn = x * cos + y * sin
    yn = - x * sin + y * cos
    return xn, yn


################################## function that use other functions ######

# A function to generate a multipeak fit function
def createmultipeakfit(fit_func=gauss, peaknum=3):
    """
    This function generates a multipeak function and give it as result back to the user. 

    Keyword arguments:
    fit_func -- FitFunction class that is one peak
    peaknum -- int how many peaks you want

    Return value:
    multipeak function a FitFunction class

    """
    multipeak = FitFunction()
    multipeak.name = 'multipeak function of '+ str(peaknum) + ' ' + FitFunction.name
    multipeak.detail = 'Sum over ' + str(peaknum) + ' ' + FitFunction.detail
    multipeak.p = [None] * (peaknum*(len(fit_func.p)-1)+1)
    def getinits(x, y):
        result = []
        for i in range(peaknum):
            pinit = fit_func.getinits(x, y)[:-1]
            pinit[1] = (x.max()-x.min())*(i+1)/float(peaknum+1) + x.min()
            result = np.append(result, pinit)
        result = np.append(result, y.min())
        return result
    multipeak.getinits = getinits
    def execute(p, x):
        y = 0.
        for i in range(peaknum):
             y + fit_func.execute(np.append(p[i*(len(fit_func.p)-1):(i+1)*(len(fit_func.p)-1)], 0.), x)
        return y + p[-1]
    multipeak.execute = execute
    return multipeak
	


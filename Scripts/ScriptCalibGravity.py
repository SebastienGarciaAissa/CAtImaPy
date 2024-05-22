#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# Script to be loaded in CAtImaPy for calibration of camera µm/pixel by using free fall 
# Sebastien Garcia 2023

import scipy.optimize as opt


pos = self.Imaging.cloudPositionsumAvList
pos_err = self.Imaging.cloudPositionsumAvErrList
# nb_scan = self.Imaging.scans
time_data = self.Imaging.T_TOFmsaxis 
time_fit = np.linspace(0,time_data[-1],200)

# Norm = np.sqrt(pos[:,0]**2+pos[:,1]**2)
Norm = pos[:,0]
params,_ = opt.curve_fit(lambda t,g,off : -g*(t)**2/2 + off ,time_data,  Norm, p0 = [9.81, Norm[0]])
print('g = %.2f m.s-2'%params[0])
print(params[1])

plt.figure()
plt.plot(time_data, Norm, 'o')
plt.plot(time_fit, -params[0]*(time_fit)**2/2 + params[1], label = 'g = %.2f m.s-2'%params[0])
plt.xlabel('time in µs')
plt.ylabel('Pos in µm')
plt.legend()


#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 09:57:49 2017

@author: ron


Here is a script that is meant to help in the task of evaluating the quality of
PyPTV calibration. 

Once a PyPTV experiment folder is ready and a calibration is established, the 
evaluation here is made by comparing known points of calibration (i.e. calblock)
points, with points that were determined using images of the calibration target
(i.e. dt_lsq points). To generate the dt_lsq points load the calibration images
as the ones to analyze first. Then process the images with:
    
    image coords -> corespondeces -> 3D Positions

The script here is used by loading the point files with the functions:
read_dt_lsq(), and read_calblock(). After that use the function pair_cal_points()
to match points from both sets. 

The evaluation itself is made by first plotting the points in 3D with  
plot_cal_points(). The distribution of errors can the be examined with the
plot_cal_err_histogram() function
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D





def read_dt_lsq(file_path):
    """
    will read a PyPTV dt_lsq file and return the points as a list of
    numpy arrays
    
    inputs
    ======
    file_path (string) - absolute path to dt_lsq file
    
    output
    ======
    points (list) - list of numpy (3,1) arrays with (x,y,z) coordinates
    """
    f = open(file_path,'r')
    N_particles = int(f.readline().strip())
    points = []
    
    for i in range(N_particles):
        l = f.readline().strip().split()
        point = np.array([l[1], l[2], l[3]], dtype=float) 
        points.append(point)
    
    f.close()
    
    return points




def read_calblock(file_path):
    """
    will read a PyPTV calbloack file and return the points as a list of
    numpy arrays
    
    inputs
    ======
    file_path (string) - absolute path to dt_lsq file
    
    output
    ======
    points (list) - list of numpy (3,1) arrays with (x,y,z) coordinates
    """
    f = open(file_path,'r')
    a = f.readlines()
    f.close()
    points = []
    
    for i in range(len(a)):
        l = a[i].strip().split()
        try:
            point = np.array([l[1], l[2], l[3]], dtype=float) 
        except:
            print('last data', l)
            raise ValueError('bad line in calblock file')
        points.append(point)
        
    return points
    



def pair_cal_points(calblock_pnts, dt_lsq_pnts, max_dist = 3.0):
    '''
    will determine pairs of points from the dt_lsq file and the known calblock
    file. for each point in the dt_lsq file, will find the closest point to it 
    from the calblock points.
    
    inputs
    ======
    calblock_pnts (list) - a list of array(3,1) points from a calblock file
    dt_lsq_pnts (list) - a list of array(3,1) points for a dt_lsq file
    max_dist (float) - the maximum distance that can be regarded a pair
    
    output
    ======
    pairs_list (list) - a list of pairs of points. the first is a calbclock
                       point and the second a dt_lsq point
    
    '''
    N_cb = len(calblock_pnts)
    N_dt = len(dt_lsq_pnts)
    N_pairs = min(N_cb, N_dt)
    
    dist_mat = np.zeros( (N_cb, N_dt) )
    index_mat = np.zeros( (N_cb, N_dt), dtype=[ ('i', 'i4'),('j','i4' )])
    for i in range(dist_mat.shape[0]):
        for j in range(dist_mat.shape[1]):
            dist_mat[i,j] = np.linalg.norm(calblock_pnts[i] - dt_lsq_pnts[j])
            index_mat[i,j] = (i,j)
                        
    pairs_list = []
    for i in range(N_pairs):
        d = np.amin(dist_mat)
        if d < max_dist:
            w = np.where(dist_mat == np.amin(dist_mat))
            i_ = index_mat['i'][w[0][0], w[1][0]]
            j_ = index_mat['j'][w[0][0], w[1][0]]
            pairs_list.append( (calblock_pnts[i_],
                                dt_lsq_pnts[j_]) )
        
            dist_mat = np.delete(dist_mat, w[0][0], axis=0)
            dist_mat = np.delete(dist_mat, w[1][0], axis=1)
            index_mat = np.delete(index_mat, w[0][0], axis=0)
            index_mat = np.delete(index_mat, w[1][0], axis=1)
        else: break
    return pairs_list
    




def plot_cal_points(pairs_list):
    '''
    plot a 3D scatter plot of calblock points (red) and dt_lsq points (blue).
    
    input
    =====
    pairs_list (list) - output from pair_cal_points()
    
    output
    ======
    fig, ax - matplotlib figure and axis objets 
    '''
    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    for p in pairs_list:
        ax.plot([p[0][0]], [p[0][2]], [p[0][1]], 'xr')
        ax.plot([p[1][0]], [p[1][2]], [p[1][1]], 'xb')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Z')
    ax.set_zlabel('Y')
    
    return fig, ax
    
    
    
    
def plot_cal_err_histogram(pairs_list):
    '''
    plot a 3D scatter plot of calblock points (red) and dt_lsq points (blue).
    
    input
    =====
    pairs_list (list) - output from pair_cal_points()
    
    output
    ======
    fig, ax - matplotlib figure and axis objets 
    '''
    
    dx,dy,dz = [],[],[]
    
    for p in pairs_list:
        dx.append(p[0][0] - p[1][0])
        dy.append(p[0][1] - p[1][1])
        dz.append(p[0][2] - p[1][2])
    
    fig,ax = plt.subplots()
    
    lbls = [r'x',r'y',r'z']
    for e,lst in enumerate([dx,dy,dz]):
        m,s = np.mean(lst), np.std(lst)
        h=ax.hist(lst,bins=8,histtype= 'step', lw=3,
                  label=r'$\langle %s \rangle=%0.3f, \sigma_{%s}=%0.3f$'%(lbls[e],m,lbls[e],s))
        #h = np.histogram(lst,bins=10)
        #x,y = (h[1][:-1] + h[1][1:])*0.5 , h[0]
        #ax.plot(x,y, '-o', lw=2, 
                #label=r'$%s:$ $\mu=%0.0e, \sigma=%0.1e$'%(lbls[e],m,s))
    ax.legend(loc='best')
    return fig, ax
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
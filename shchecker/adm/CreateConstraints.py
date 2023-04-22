# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 16:03:40 2019

@author: Nur Imtiazul Haque
"""
# importing libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from scipy.spatial import ConvexHull, convex_hull_plot_2d
import matplotlib.pyplot as plt
import os
from z3 import *
from sklearn import preprocessing

class CreateConstraints:
    def __init__(self, datasetFile, eps, minPts):
        self.dataset = pd.read_csv(datasetFile)
            
    def lineEquation(x,y,x_1,y_1,x_2,y_2):
        return ( (x-x_1)/(x_1-x_2) == (y-y_1)/(y_1-y_2) ) 
   
    def const( p, q, initial_point, final_point ):
        if final_point[1] < initial_point[1]:
            #swap
            temp = initial_point
            initial_point = final_point
            final_point = temp
            
        a = -(final_point[1]-initial_point[1])
        b = (final_point[0]-initial_point[0])
        c = -(a *initial_point[0]  + b * initial_point[1])
        
        a=round(a,4)
        b=round(b,4)
        c=round(c,4)
        
        constraint_1 = a * ( M[p]+dx[p] ) + b * ( M[q]+dx[q] ) + c >= 0       
        constraint_2 = ( M[q]+dx[q] ) < final_point[1]
        constraint_3 = ( M[q]+dx[q] ) >= initial_point[1]
        return constraint_1, constraint_2, constraint_3  


    def constraintCreation():
        # feature count
        number_of_features = dataset.shape[1]-1
        
        # feature
        x= dataset.iloc[:,:-1]
        # label
        y= dataset.iloc[:,-1]
        
        ## parameters
        eps=0.5
        minPts=5
        
        # preprocesing
        y= preprocessing.LabelEncoder().fit_transform( y )
        
        M=[]
        dx=[]
        
        for i in range(number_of_features):
            M.append(Real('M_'+str(i)))
            dx.append(Real('dx_'+str(i)))
        
        state_constraints=[]
        
        for state in range(len(states)):
            final_constraints=[]
            
            for i in range(number_of_features-1):
                for j in range(i+1,number_of_features):       
                    prefix = "Boundaries/"+ str(states[state]) +"/" + str(i) + "_" +str(j)+'/'
                    
                    files=os.listdir(prefix)
                    
                    if(len(files)==0):
                        continue
                    xor_constraints=[]
                    for f in range(len(files)):
                        count=0        
                        
                        points=[]    
                        for point in open(prefix+files[f]):
                            point=point.split()            
                            points.append(tuple((float(point[0]),float(point[1]))))
                        points=np.asarray(points) 
                        
                        constraints=[]
                        for k in range(points.shape[0]-1):
                            constraints.append(const(i, j, points[k], points[k+1]))
                        
                        and_constraints=[]
                        for k in range( len( constraints )):            
                            and_constraints.append( And( constraints[k][0], constraints[k][1], constraints[k][2] ) )
                        
                        if len(and_constraints) == 0:
                            continue
                        
                        current = and_constraints[0]
                        xor_constraint = and_constraints[0]
                        
                        for k in range( len( and_constraints )-1 ):
                            xor_constraint=Xor(current,and_constraints[k+1])
                            current=xor_constraint
                            
                        xor_constraints.append(xor_constraint)    
                    
                    boundary_constraints=[]
                    for f in range( len( files ) ):
                        for point in open( prefix + files[f] ):
                            point=point.split()
                            constraint_1= M[i] == float(point[0])
                            constraint_2= M[j] == float(point[1])
                            boundary_constraints.append(And(constraint_1,constraint_2))
                      
                    or_boundary_constraints = Or(boundary_constraints)
                    or_constraints = Or(xor_constraints)
                    final_constraints.append( Or( or_constraints, or_boundary_constraints ) )
        
            state_constraints.append( And( final_constraints ) )
        return state_constraints
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from scipy.spatial import ConvexHull, convex_hull_plot_2d
import matplotlib.pyplot as plt
import re
import os
import csv
from sklearn import preprocessing
import time
from sklearn.cluster import KMeans

class CreateCluster:
    def __init__(self, datasetFile, clusteringMethod):
        self.dataset = pd.read_csv(datasetFile)
        # clusteringMethod could be 'kMeans' or 'DBSCAN'
        self.clusteringMethod = clusteringMethod
        
    def setParamsForDBSCAN(self, eps, minPts):
        self.eps = eps
        self.minPts = minPts
        
    def setParamsForKMeans(self, numClusters):
        self.numClusters = numClusters
        
    def clusterCreation(self, states):
        # for counting time
        tic = time.perf_counter()
        # all columns other than the last one are features columns
        number_of_features = self.dataset.shape[1]-1
        # features
        x= self.dataset.iloc[:,:-1]
        # label
        y= self.dataset.iloc[:,-1]
        # label encoding
        y= preprocessing.LabelEncoder().fit_transform(y)

        os.mkdir("Clusters")
        for state in range(len(states)):
            os.mkdir("Clusters/"+ str(states[state]))
        
        for state in range(len(states)):
            for i in range(number_of_features-1):
                for j in range(i+1, number_of_features):
                    # combination of pair of features
                    x = self.dataset.iloc[y==state, np.r_[i,j]].values
                    
                    # directory for separating and orgranizing cluster points
                    dir=os.mkdir("Clusters/" + str(states[state])+"/"+str(i) + "_" +str(j)+'/')
                    
                    if self.clusteringMethod == 'DBSCAN':
                        db = DBSCAN(eps = self.eps, min_samples = self.minPts).fit(x)
                        
                    elif self.clusteringMethod == 'KMeans':
                        db = KMeans(n_clusters= self.numClusters, random_state=0).fit(x)
                        
                    # number of clusters in labels, ignoring noise points
                    labels = db.labels_
                    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    n_noise = list(labels).count(-1)
                                        
                    for cluster in range(n_clusters):
                        points = []
                        for k in range(len(labels)):
                            if labels[k] == cluster:
                                points.append(X[k])
                        points=np.array(points)
                        
                        if len(points > 0):
                            f = open("Clusters/"+ str(states[state])+"/"+str(i) + "_" +str(j)+'/'+str(cluster)+".txt", "w")
                            for data in points:
                                f.write(str(data[0])+' '+str(data[1])+'\n')
                            f.close()
        toc = time.perf_counter()
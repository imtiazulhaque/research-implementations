import numpy as np
import pandas as pd
from dcm import *
from adm import *

# counting SAT and UNSAT results
n_sat=0
n_unsat=0

# dcmType contains "DT": Decision Tree, "NN": Neural Network, or "LR": Logistic Regression

# preprocessing, model creation
if dcmType == "DT":
    modeling = DTModeling(dataset, sample, test_size)
    modeling.dtModeling
    
elif dcmType == "LR":
    modeling = LRModeling(dataset, sample, test_size)
    modeling.lrModeling
    
elif dcmType == "NN":
    modeling = NNModeling(dataset, sample, test_size, epochs, batch_size, nodes_in_hidden_layers, activation_functions)
    modeling.nnModeling    

# formal modeling of dcm and determining label
label = modeling.formalModeling()

# z3 solver uses SMT theory
s=Solver()

# creating cluster for 
cluster = CreateCluster(datasetFile, clusteringMethod)
# if clusteringMethod = 'KMeans'
cluster.setParamsForKMeans(numClusters)
# if clusteringMethod = 'DBSCAN'
cluster.setParamsForDBSCAN(eps, misPts) 

# cluster creation
# states containts all possible disease labels
cluster.clusterCreation(states)

# creating constraints for adm based on clusteringMethod
# clusteringMethod could be "KMeans" or "DBSCAN"
# CreateContraints returns state constraints 
state_constraints = CreateConstraints(datasetFile, clusteringMethod)

s.add(state_constraints[label])

for j in range(number_of_features):
    # sample contains the feature values for the samples
    s.add(M[j] == sample[i][j] )
    s.add(dx[j] / sample[i][j] <=  (threshold / 100))
    s.add(dx[j] / X[i][j] >=  -( threshold / 100))
if (s.check() == sat):
    print(i, sample[i], s.model())
if s.check()==sat:
    n_sat+=1
else:
    n_unsat+=1
    
print("#SAT: ",n_sat)
print("#UNSAT ",n_unsat)   
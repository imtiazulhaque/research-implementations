# importing libraries
import csv
import pandas as pd
import numpy as np
import math
from z3 import *
from sklearn.linear_model import LogisticRegression
from fractions import Fraction
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.utils.extmath import softmax

class LRModeling:
  def __init__(self, dataset, input_val, test_size):
    self.dataset = dataset
    self.test_size = test_size
    self.input_val = input_val
    
  # z3-solver returns model output in fraction format
  # converting z3 model outputs into floating point numbers
  def toFloat(self, str):
    return float(Fraction(str))

  def exponential(self, val):
      result = 0
      for i in range(100):
        result = result + val**i / math.factorial(i)   
      return result
  
  def softMax(self, index, values):
      sum =  0
      for value in values:
        sum =  sum + self.exponential(value)
      return self.exponential(values[index]) / sum

  def lrPreprocessing(self):    
    # features
    self.X = self.dataset.iloc[:,:-1]
    # labels
    self.y= preprocessing.LabelEncoder().fit_transform( self.dataset.iloc[:,-1] )

    # counting input output nodes
    num_inp_nodes = self.X.shape[1]
    num_out_nodes = len(np.unique(self.y))

    # train-test spilitting
    self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size = self.test_size, random_state = 0)

    self.nodes_in_layers = [num_inp_nodes]
    self.nodes_in_layers.append(num_out_nodes)

  def lrModeling(self):
    self.lrPreprocessing()
    self.model = LogisticRegression(random_state=0).fit(self.X, self.y)
  
  def formalModeling(self):
    solver = Solver()
    z3_input = [ [ Real( 'z3_input_' + str(i) + '_' + str(j)) for j in range( self.nodes_in_layers[i])] 
                for i in range(len(self.nodes_in_layers) ) ] 
    z3_output = [ [ Real( 'z3_output_' + str(i) + '_' + str(j)) for j in range( self.nodes_in_layers[i])] 
                for i in range(len(self.nodes_in_layers) ) ] 
    z3_bias = [ [ Real( 'z3_bias_' + str(i) + '_' + str(j)) for j in range( self.nodes_in_layers[i+1])] 
              for i in range(len(self.nodes_in_layers ) -1 ) ] 
    z3_weight =  [ [ [Real( 'z3_weight_' + str(i) + '_' + str(j) + '_' + str(k) ) 
              for k in range (self.nodes_in_layers[i+1]) ] for j in range( self.nodes_in_layers[i] )  ]  
              for i in range (len(self.nodes_in_layers) - 1) ]

    ## input and output value constraint of layer 0
    for i in range(len(z3_input[0])): solver.add( z3_input[0][i] == input_val[0][i] )
    for i in range(len(z3_output[0])): solver.add( z3_output[0][i] == z3_input[0][i] )


    # assigning biases
    for i in range( len(z3_bias) ):
      for j in range( len(z3_bias[i]) ):
        solver.add( z3_bias[i][j] == self.model.layers[i].get_weights()[1][j] )

    # assigning weights
    for i in range( len(z3_weight) ):
      for j in range( len(z3_weight[i]) ):
        for k in range( len(z3_weight[i][j]) ):
          solver.add( z3_weight[i][j][k] == self.model.layers[i].get_weights()[0][j][k] )

    for i  in range( len(self.nodes_in_layers) -1 ):
      for j in range ( self.nodes_in_layers[i+1] ):
        temp = 0
        for k in range ( self.nodes_in_layers[i] ):
          temp = temp + z3_weight[i][k][j] * z3_output[i][k]
        temp = temp + z3_bias[i][j]
        solver.add( z3_input[i+1][j] == temp)
        
        
        arr = []
        for l in range(len(z3_input[i+1])):
          arr.append(z3_input[i+1][l]) 
        solver.add(z3_output[i+1][j] == self.softMax(j, arr))
    solver.check()
    
    final_layer = len(z3_output) - 1
    
    label = -1
    maxm = 0

    # finding argmax and assigning it as a label
    for i in range(len(z3_output[final_layer])):
      # determining current softmax value
      cVal = self.toFloat(str( solver.model()[z3_output[final_layer][i]]))
      if cVal > maxm:
          maxm = cVal
          label = i
      
    # returning the label
    return label
    final_layer = len(z3_output) - 1
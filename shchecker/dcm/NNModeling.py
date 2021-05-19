# importing libraries
import csv
import pandas as pd
import numpy as np
import math
from z3 import *
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense
from tensorflow.python.keras.wrappers.scikit_learn import KerasClassifier
from tensorflow.keras.utils import to_categorical
from fractions import Fraction
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.utils.extmath import softmax

class NNModeling:
  def __init__(self, dataset, input_val, test_size, epochs, batch_size, nodes_in_hidden_layers, activation_functions ):
    self.dataset = dataset
    self.test_size = test_size
    self.input_val = input_val
    self.epochs = epochs
    self.batch_size = batch_size
    self.nodes_in_hidden_layers = nodes_in_hidden_layers
    self.activation_functions = activation_functions

  # z3-solver returns model output in fraction format
  # converting z3 model outputs into floating point numbers
  def toFloat(self, str):
    return float(Fraction(str))

  # rectified linear units activation function
  def relu(self, val):
      return val * (val > 0)

  def exponential(self, val):
      result = 0
      for i in range(100):
        result = result + val**i / math.factorial(i)   
      return result

  def sigmoid(self, val):
      return 1 / (1 + self.exponential(-val) )

  def softMax(self, index, values):
      sum =  0
      for value in values:
        sum =  sum + self.exponential(value)
      return self.exponential(values[index]) / sum

  def nnPreprocessing(self):    
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
    for nodes in self.nodes_in_hidden_layers:
      self.nodes_in_layers.append(nodes)
    self.nodes_in_layers.append(num_out_nodes)

  def nnModeling(self):
    self.nnPreprocessing()
    self.model = Sequential()

    self.model.add( Dense(self.nodes_in_layers[1], input_dim = self.nodes_in_layers[0], activation = self.activation_functions[0] ))

    for i in range(2, len(self.nodes_in_layers) ):
      self.model.add( Dense(self.nodes_in_layers[i], activation = self.activation_functions[i - 1] ))
    self.model.compile( optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'],)
    self.model.fit( self.X_train, to_categorical(self.y_train), epochs=self.epochs, batch_size=self.batch_size, verbose=0)
    self.model.evaluate(self.X_test, to_categorical(self.y_test))
  
  def formalModeling(self):
    #self.nn_modeling()

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

    # determining hidden and output layer input and output constraints
    for i  in range( len(self.nodes_in_layers) -1 ):
      for j in range ( self.nodes_in_layers[i+1] ):
        temp = 0
        for k in range ( self.nodes_in_layers[i] ):
          temp = temp + z3_weight[i][k][j] * z3_output[i][k]
        temp = temp + z3_bias[i][j]
        solver.add( z3_input[i+1][j] == temp)
        
        if self.activation_functions[i]=='relu':
          solver.add(z3_output[i+1][j] == self.relu(z3_input[i+1][j]) )

        elif self.activation_functions[i]=='softmax':
          arr = []
          for l in range(len(z3_input[i+1])):
            arr.append(z3_input[i+1][l]) 
          solver.add(z3_output[i+1][j] == self.softMax(j, arr))
    print(solver)
    solver.check()
    print("Keras model output: ")
    print(self.model.predict(input_val))

    print("Z3 model output: ")
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
      
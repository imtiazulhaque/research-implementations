from sklearn.tree import DecisionTreeClassifier
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
import seaborn as sns
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.externals.six import StringIO  
from sklearn import tree
import pydot 
from z3 import *

class DTModeling:
    def __init__(self, dataset, input_val, test_size ):
        self.dataset = dataset
        self.test_size = test_size
        self.input_val = input_val
        
    def getRules(self, dtc, df):
        rules_list = []
        values_path = []
        values = dtc.tree_.value
    
        def revTraverseTree(tree, node, rules, pathValues):
            try:
                prevnode = tree[2].index(node)           
                leftright = '<='
                pathValues.append(values[prevnode])
            except ValueError:
                # failed, so find it as a right node - if this also causes an exception, something's really f'd up
                prevnode = tree[3].index(node)
                leftright = '>'
                pathValues.append(values[prevnode])
    
            # now let's get the rule that caused prevnode to -> node
            p1 = tree[0][prevnode]    
            p2 = tree[1][prevnode]    
            #rules.append(str(p1) + ' ' + leftright + ' ' + str(p2))
            rules.append([p1, leftright, p2])
    
            # if we've not yet reached the top, go up the tree one more step
            if prevnode != 0:
                revTraverseTree(tree, prevnode, rules, pathValues)
    
        # get the nodes which are leaves
        leaves = dtc.tree_.children_left == -1
        leaves = np.arange(0,dtc.tree_.node_count)[leaves]
    
        # build a simpler tree as a nested list: [split feature, split threshold, left node, right node]
        thistree = [dtc.tree_.feature.tolist()]
        thistree.append(dtc.tree_.threshold.tolist())
        thistree.append(dtc.tree_.children_left.tolist())
        thistree.append(dtc.tree_.children_right.tolist())
    
        # get the decision rules for each leaf node & apply them
        for (ind,nod) in enumerate(leaves):
    
            # get the decision rules
            rules = []
            pathValues = []
            revTraverseTree(thistree, nod, rules, pathValues)
    
            pathValues.insert(0, values[nod])      
            pathValues = list(reversed(pathValues))
    
            rules = list(reversed(rules))
    
            rules_list.append(rules)
            values_path.append(pathValues)
    
        return (rules_list, values_path)
    
    def dtPreprocessing( self ):    
    # features
        self.X = self.dataset.iloc[:,:-1]
        # labels
        self.y= preprocessing.LabelEncoder().fit_transform( self.dataset.iloc[:,-1] )
    
        # counting input features and output labels
        self.num_inp_features = self.X.shape[1]
        self.num_out_lables = len(np.unique(self.y))
    
        # train-test spilitting
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size = self.test_size, random_state = 0)
        
    def dtModeling( self ):  
        self. dtPreprocessing()
        self.model = DecisionTreeClassifier(random_state=0)
        self.model.fit(self.X_train, self.y_train)
        y_pred = self.model.predict( self.X_test )
        score = accuracy_score(self.y_test, y_pred)
        print("Accruracy score ", score)

        # plotting confusion matrix
        conf_matrix = confusion_matrix(self.y_test, y_pred)
        sns.heatmap(conf_matrix, annot=True, fmt='d')

    def formalModeling( self ):
        self.dt_modeling()
        s = Solver()
        z3_input = [Real('input_'+str(i)) for i in range( self.num_inp_features )]
        z3_output = Int( 'z3_output' )
        
        for i in range ( len(self.get_rules(self.model, self.dataset)[0] ) ):
            and_rules = []
            
            for j in range ( len(self.get_rules(self.model, self.dataset)[0][i] ) ):
                #print(( type( get_rules(model, dataset)[0][i][j]) ) )
                if self.get_rules(self.model, self.dataset)[0][i][j][1] == '<=':        
                    and_rules.append( z3_input[ self.get_rules(self.model, self.dataset)[0][i][j][0] ] <= 
                                               self.get_rules(self.model, self.dataset)[0][i][j][2] )
                elif self.get_rules(self.model, self.dataset)[0][i][j][1] == '>':        
                    and_rules.append( z3_input[ self.get_rules(self.model, self.dataset)[0][i][j][0] ] > 
                                               self.get_rules(self.model, self.dataset)[0][i][j][2] )
            length = len(self.get_rules(self.model, self.dataset)[1][i])
            label = np.argmax( np. asarray(self.get_rules(self.model, self.dataset)[1][i][length - 1]) )
            s.add( Implies( And( and_rules ), z3_output ==  int(label) ) )
        
        
        for i in range( self.X.shape[1] ):
            s.add( z3_input[i] == self.input_val[0][i])
        s.check()
        
        # returning label
        return toFloat(str(solver.model()[z3_output]))
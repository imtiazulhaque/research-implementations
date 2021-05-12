"""
Created on Wed Sep 30 14:54:46 2020
@author: haque
"""

# built-n libraries
import numpy as np
import pandas as pd
import random
from z3 import *
from datetime import datetime

# user-defined libraries
import CoolingControl
import HeatingControl
import AttackHeatingControl
import Threat
import DatasetGeneration

import HVACCost
import HeatingCostCalculation


################ Temperature Processing #####################
temp_dataframe = pd.read_csv("data/Temp-Data.csv", encoding='latin1')
date_temp_data = temp_dataframe.iloc[:,0]
temp_data = temp_dataframe.iloc[:,2]
rh_data = temp_dataframe.iloc[:,3]


temp_dict = dict()
rh_dict = dict()
for i in range(len(date_temp_data)):
    month, day, year = [int(x) for x in date_temp_data[i].split('/')]
    current_date = datetime(year, month, day)
    temp_dict[current_date] = float(temp_data[i][:-1])
    rh_dict[current_date] = float(rh_data[i])
    
    
start_date = datetime(2015, 8, 26)
end_date = datetime(2016, 8, 25)

num_zones = 4
co2_fresh_air = 400
temp_fresh_air = 16.67
rh_mixed = 71
rh_supply = 45


main_entrance_data = pd.DataFrame(DatasetGeneration.DatasetGeneration("data/Main_Entrance.csv", start_date, end_date)[0], columns=['date', 'Zone 1 People (person)'])
clemente_data = pd.DataFrame(DatasetGeneration.DatasetGeneration("data/Clemente.csv", start_date, end_date)[0], columns=['date', 'Zone 2 People (person)'])
warhol_data = pd.DataFrame(DatasetGeneration.DatasetGeneration("data/Warhol.csv", start_date, end_date)[0], columns=['date', 'Zone 3 People (person)'])
lab_data = pd.DataFrame(DatasetGeneration.DatasetGeneration("data/Main_Entrance.csv", start_date, end_date)[0], columns=['date', 'Zone 4 People (person)'])
lab_data.iloc[:,1] = (lab_data.iloc[:,1] * random.uniform(0.6,0.9)).astype(int)

dataframe = pd.merge(main_entrance_data, clemente_data, left_on='date', right_on='date')
dataframe = pd.merge(dataframe, warhol_data, left_on='date', right_on='date')
dataframe = pd.merge(dataframe, lab_data, left_on='date', right_on='date')

total_occupant = dataframe.iloc[:,1] + dataframe.iloc[:,2] + dataframe.iloc[:,3] + dataframe.iloc[:,4]
dataframe['Total People (person)'] = total_occupant

dataframe_date = dataframe.iloc[:,0]

arr = []
arr_rh = []
for i in range(len(dataframe_date)):
    current_date = dataframe_date[i]
    current_date = datetime(current_date.year, current_date.month, current_date.day)
    arr.append(temp_dict[current_date])
    arr_rh.append(rh_dict[current_date])
    

dataframe['Temperature'] = arr
dataframe['Rh'] = arr_rh

for i in range(num_zones):
    dataframe['Zone ' + str(i + 1) + ' CO2 Setpoint (ppm)'] = 1000
    dataframe['Zone ' + str(i + 1) + ' Temperature Setpoint (degree C)'] = 24
    
    
#dataframe.to_csv('data/COD.csv', index =False)


avg_cost = 7.02 / 6
#avg_cost = 1

total_cost = 0
total_control_cost = 0
total_attack_cost = 0

for i in range (len(dataframe)):
    print(i)
    zone_info = pd.DataFrame(dataframe.iloc[i,:]).T
    att_zone_info = zone_info.copy()
    
    temp_fresh_air = float(zone_info['Temperature'])
    rh_mixed = float(zone_info['Rh'])
    
    att_zone_info.iloc[0,1:num_zones + 1] = Threat.Threat(zone_info, num_zones, co2_fresh_air, temp_fresh_air)
    
    zone_info = pd.DataFrame(dataframe.iloc[i,:]).T

    # for KTH dataset, 'data/KTH.csv'
    zone_info.to_csv('data/COD.csv', index =False)
    att_zone_info.to_csv('data/Att-COD.csv', index =False)
    
    control_cost = avg_cost * HeatingControl.HeatingControl('data/COD.csv', num_zones, co2_fresh_air, temp_fresh_air, rh_mixed, rh_supply)
    cooling_control_cost = avg_cost * CoolingControl.CoolingControl('data/COD.csv', num_zones, co2_fresh_air, temp_fresh_air, rh_mixed, rh_supply)
    
    if cooling_control_cost > control_cost:
        control_cost = cooling_control_cost
    
    
    attack_cost = avg_cost * AttackHeatingControl.AttackHeatingControl('data/COD.csv','data/Att-COD.csv', num_zones, co2_fresh_air, temp_fresh_air, rh_mixed, rh_supply)
    
    total_control_cost += control_cost
    total_attack_cost += attack_cost
    total_cost = (attack_cost - control_cost)


# =============================================================================
# co2_fresh_air = 400
# temp_fresh_air = 16.67
# rh_mixed = 71
# rh_supply = 45
# temp_mixed = 16.67
# temp_supply = 30.65 
# m_coil = 4.67
# temp_coil = 6
# v_mixed_air = 20
# x = HVACCost.HVACCost(temp_mixed, rh_mixed, temp_supply, rh_supply, m_coil, temp_coil, v_mixed_air / 2118.87, "kWh")
# y = HeatingCostCalculation.HeatingCostCalculation(temp_mixed, rh_mixed, temp_supply, rh_supply, m_coil, temp_coil, v_mixed_air / 2118.87, "kWh")
# print(x,y)        
# =============================================================================

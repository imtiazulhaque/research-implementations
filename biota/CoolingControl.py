"""
Created on Fri Oct  2 00:27:24 2020

@author: haque
"""

import pandas as pd
import numpy as np
from z3 import *
import statistics

import CoolingCostCalculation
import HVACCost

def CoolingControl(data_file, num_zones, co2_fresh_air, temp_fresh_air, rh_mixed, rh_supply):
    ################## constants ##################################
    SAMPLING_TIME = 10                  # sampling time (minute)
    CP_AIR = 1.026
    
    zone_info = pd.read_csv(data_file)
    
    zone_desc = pd.read_csv('data/Zone-Description.csv')
    zone_volume = zone_desc['Volume (cf)'].tolist()
    zone_pp_co2 = zone_desc['CO2 Emission Per Person (cfm)'].tolist()
    zone_pp_load = zone_desc['Cooling Load Per Person(kW)'].tolist()
    zone_equip_load = zone_desc['Cooling Load (kW)'].tolist()
    zone_occupant = [zone_info['Zone ' + str(i+1) + ' People (person)'].tolist()[0] for i in range(num_zones)]
    zone_co2_setpoint = [zone_info['Zone ' + str(i+1) + ' CO2 Setpoint (ppm)'].tolist()[0] for i in range(num_zones)]
    zone_temp_setpoint = [zone_info['Zone ' + str(i+1) + ' Temperature Setpoint (degree C)'].tolist()[0] for i in range(num_zones)]
    
    
    
    v_vent_air = [Real( 'v_vent_air_' + str(i)) for i in range(num_zones)]
    v_temp_air = [Real( 'v_temp_air_' + str(i)) for i in range(num_zones)]
    v_mixed_air = [Real( 'v_mixed_air_' + str(i)) for i in range(num_zones)]
    v_fresh_air = [Real( 'v_fresh_air_' + str(i)) for i in range(num_zones)]
    v_return_air = [Real( 'v_return_air_' + str(i)) for i in range(num_zones)]
    
    
    temp_supply_air = [ Real( 'temp_supply_air_' + str(i)) for i in range(num_zones)]
    temp_mixed_air = [ Real( 'temp_mixed_air_' + str(i)) for i in range(num_zones)]
    co2_mixed_air = [ Real( 'co2_mixed_air_' + str(i)) for i in range(num_zones)]
    
    i = 0
    
    s = Solver()
      
    for i in range(num_zones):
        ############### v_vent_air ###############################
        s.add(zone_occupant[i] * ((zone_pp_co2[i] * 1000000 * SAMPLING_TIME) / zone_volume[i]) == 
               (zone_co2_setpoint[i] - (( 1 - ( v_vent_air[i] * SAMPLING_TIME ) / zone_volume[i]) * zone_co2_setpoint[i] +  
                                        ( v_vent_air[i] * SAMPLING_TIME * co2_fresh_air) / zone_volume[i])))
    
    
    
        ############### v_temp_air ###############################
        s.add((v_temp_air[i] * CP_AIR * 11 ) / (0.89 * 2118.87) == ( zone_equip_load[i] + zone_occupant[i] * zone_pp_load[i]))
                
                
        ############### v_mixed_air ###############################
        s.add(zone_occupant[i] * ((zone_pp_co2[i] * 1000000 * SAMPLING_TIME ) / zone_volume[i]) == 
              (zone_co2_setpoint[i] - (( 1 - ( v_mixed_air[i] * SAMPLING_TIME ) / zone_volume[i]) * zone_co2_setpoint[i] + 
                                     ( v_mixed_air[i] * SAMPLING_TIME * co2_mixed_air[i]) / zone_volume[i])))
         
        s.add((v_mixed_air[i] * CP_AIR * (zone_temp_setpoint[i] - temp_supply_air[i]) ) / (0.89 * 2118.87) == ( zone_equip_load[i] + zone_occupant[i] * zone_pp_load[i]))
        
        s.add(v_mixed_air[i] == v_return_air[i] + v_fresh_air[i])
        s.add(co2_mixed_air[i] == zone_co2_setpoint[i] * (v_return_air[i] / v_mixed_air[i]) + co2_fresh_air * (v_fresh_air[i] / v_mixed_air[i]))
        s.add(temp_mixed_air[i] == zone_temp_setpoint[i] * (v_return_air[i] / v_mixed_air[i]) + temp_fresh_air * (v_fresh_air[i] / v_mixed_air[i]))
         
        
        ############### temperature control algorithm ############
        s.add(Implies(v_vent_air[i] >= v_temp_air[i] , v_return_air[i] == 0))
        s.add(Implies(v_vent_air[i] < v_temp_air[i] ,  temp_supply_air[i] == 13))
        
        ############### other constraints ########################
        s.add(v_return_air[i] >= 0)
        s.add(temp_supply_air[i] >= 13)
    
    s.check()
    #print(s.check())
    #print(s.model())   
    total_cost = 0
    for i in range(num_zones):
        v_vent_air[i] = float(Fraction(str(s.model()[v_vent_air[i]])))
        v_temp_air[i] = float(Fraction(str(s.model()[v_temp_air[i]])))
        
        v_mixed_air[i] = float(Fraction(str(s.model()[v_mixed_air[i]])))
        temp_mixed_air[i] = float(Fraction(str(s.model()[temp_mixed_air[i]])))
        
        co2_mixed_air[i] = float(Fraction(str(s.model()[co2_mixed_air[i]])))
        v_return_air[i] = float(Fraction(str(s.model()[v_return_air[i]])))
        v_fresh_air[i] = float(Fraction(str(s.model()[v_fresh_air[i]])))
        
        temp_supply_air[i] = float(Fraction(str(s.model()[temp_supply_air[i]])))
        
        temp_mixed = temp_mixed_air[i]      # temperature of mixed air (degree C)
        #rh_mixed = 70                       # relative humidity of mixed air (percentage)
        temp_supply = temp_supply_air[i]    # temperature of supply air (degree C)
        #rh_supply = 45                      # relative humidity of supply air (percentage)
        m_coil = 4.67                       # cooling water mass flow rate in coil (kg/s)
        temp_coil = 6                       # cooling water inlet temperature in coil (degree C)
        #print("y", v_vent_air[i])
        
        #print("vent", v_vent_air[i])
        #print("temp", v_temp_air[i])
        #print("co2 mixed air", co2_mixed_air[i])
        #print("v mixed air", v_mixed_air[i])
        #print("temp mixed air", temp_mixed_air[i])
        
        #print("v return air", v_return_air[i])
        #print("v fresh air", v_fresh_air[i])
        
        
        #cost = hc.hvac_cost(temp_mixed, rh_mixed, temp_supply, rh_supply, m_coil, temp_coil, v_mixed_air[i] / 2118.87, "kW")
        cost = CoolingCostCalculation.CoolingCostCalculation(temp_mixed, rh_mixed, temp_supply, rh_supply, m_coil, temp_coil, v_mixed_air[i] / 2118.87, "kWh")
        total_cost += cost
    return total_cost
"""
Created on Fri Oct  2 11:58:04 2020

@author: haque
"""

import pandas as pd
import numpy as np
from z3 import *
import statistics

# =============================================================================
# num_zones = 4
# co2_fresh_air = 400
# temp_fresh_air = 33
# rh_mixed = 70
# rh_supply = 45
# 
# dataframe =  pd.read_csv('data/COD.csv')
# i = 0
# zone_info = dataframe.iloc[i:i+1,:]
# =============================================================================


def Threat(zone_info, num_zones, co2_fresh_air, temp_fresh_air):
    SAMPLING_TIME = 10                # sampling time (minute)
    CP_AIR = 1.026
    
    
    zone_desc = pd.read_csv('data/Zone-Description.csv')
    zone_volume = zone_desc['Volume (cf)'].tolist()
    zone_pp_co2 = zone_desc['CO2 Emission Per Person (cfm)'].tolist()
    zone_pp_load = zone_desc['Cooling Load Per Person(kW)'].tolist()
    zone_equip_load = zone_desc['Cooling Load (kW)'].tolist()
    zone_max_occupant = zone_desc['Maximum Occupancy (person)'].tolist()
    
    
    zone_occupant = [zone_info['Zone ' + str(i+1) + ' People (person)'].tolist()[0] for i in range(num_zones)]
    zone_co2_setpoint = [zone_info['Zone ' + str(i+1) + ' CO2 Setpoint (ppm)'].tolist()[0] for i in range(num_zones)]
    zone_temp_setpoint = [zone_info['Zone ' + str(i+1) + ' Temperature Setpoint (degree C)'].tolist()[0] for i in range(num_zones)]
    
    
    v_vent_air = [ Real( 'v_vent_air_' + str(i)) for i in range(num_zones)]
    v_temp_air = [ Real( 'v_temp_air_' + str(i)) for i in range(num_zones)]
    v_mixed_air = [ Real( 'v_mixed_air_' + str(i)) for i in range(num_zones)]
    v_fresh_air = [ Real( 'v_fresh_air_' + str(i)) for i in range(num_zones)]
    v_return_air = [ Real( 'v_return_air_' + str(i)) for i in range(num_zones)]
    
    
    att_zone_occupant = [ Real( 'att_zone_occupant_' + str(i)) for i in range(num_zones)]
    att_zone_co2 = [ Real( 'att_zone_co2' + str(i)) for i in range(num_zones)]
    temp_supply_air = [ Real( 'temp_supply_air_' + str(i)) for i in range(num_zones)]
    co2_mixed_air = [ Real( 'co2_mixed_air_' + str(i)) for i in range(num_zones)]
    
    bdx = [ Real( 'bdx' + str(i)) for i in range(num_zones)]
    
    s = Optimize()
    for i in range(num_zones):                       
        ############### v_vent_air ###############################
        s.add(att_zone_occupant[i] * ((zone_pp_co2[i] * 1000000 * SAMPLING_TIME) / zone_volume[i]) == 
               (zone_co2_setpoint[i] - (( 1 - ( v_vent_air[i] * SAMPLING_TIME ) / zone_volume[i]) * zone_co2_setpoint[i] +  
                                          ( v_vent_air[i] * SAMPLING_TIME * co2_fresh_air) / zone_volume[i])))
    
    
        ######################## v_temp_air #################################
        s.add((v_temp_air[i] * CP_AIR * 11 ) / (0.83 * 2118.87) == ( zone_equip_load[i] + att_zone_occupant[i] * zone_pp_load[i]))
        
        
        s.add(v_vent_air[i] >= 0)
        
        ################# pir sensor node attack constraint #################
        
        s.add(att_zone_occupant[i] >= 0)
        s.add(att_zone_occupant[i] <= zone_max_occupant[i])
        
        
        s.add(Implies(att_zone_occupant[i] != zone_occupant[i], bdx[i] == 1))
        s.add(Implies(att_zone_occupant[i] == zone_occupant[i], bdx[i] == 0))
    
    s.add(Sum(bdx) <= num_zones)
    #s.add(bdx[0] == 1)
    #s.add(bdx[1] == 0)
    #s.add(bdx[2] == 1)
    #s.add(bdx[3] == 0)
    
    s.add(Sum(att_zone_occupant) == sum(zone_occupant) )
    s.maximize(Sum(v_vent_air))
    
    s.check()
    
    for i in range(num_zones):
        #print("bdx",i,s.model()[bdx[i]])
        #print("Actual Person", i, zone_occupant[i])
        #print("Attacked Person", i, float(Fraction(str(s.model()[att_zone_occupant[i]]))))
        att_zone_occupant[i] = float(Fraction(str(s.model()[att_zone_occupant[i]])))
    return att_zone_occupant
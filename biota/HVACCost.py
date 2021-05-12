# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 20:10:29 2020

@author: haque
"""


"""
Created on Wed Sep 30 14:54:37 2020
@author: haque
"""

from z3 import *
import math as m

############################## Mixed Air #################################
# temp_mixed:   temperature of mixed air (degree C)
# rh_mixed:     relative humidity of mixed air (percentage)
# eth_mixed:    enthalpy of mixed air (kJ/kg)
# sv_mixed:     specific volume of mixed air (m3/kg) (dry air)
# sh_mixed:     specific humidity of mixed air (kg water vapor/ kg dry air)
# m_air_mixed:  dry air mass flow rate of mixed air (kg/s)
# v_air_mixed:  dry air volume flow rate of mixed air (m^3/s)


############################## Supply Air #################################
# temp_supply:    temperature of supply air (degree C)
# rh_supply:      relative humidity of supply air (percentage)
# eth_supply:     enthalpy of mixed air (kJ/kg)
# sv_supply:      specific volume of mixed air
# sh_mixed:       specific humidity of supply air (kg water vapor/ kg dry air)

############################## Condenser ##################################
# temp_cond:      condenser water temperature (degree C)
# eth_cond:       enthalpy of condensed water (kJ/kg)
# m_cond:         condensate water mass flow rate (kg/s)
# cp_water:       water heat capacity (kJ/kg.K)
    

############################### Coil ######################################
# m_coil:         cooling water mass flow rate in coil (kg/s)
# temp_coil:      cooling water inlet temperature in coil (degree C)
# spht_coil:      specific heat capacity of water in coil (kJ/kg.K)


########################### Chilling tower ################################
# temp_chil:      input temperature of chilling tower (degree C)


################################# Costs ###################################
# cooling_load:   cooling load (kW)
# chiller_load:   cooling load (kW)


def HVACCost( temp_mixed, rh_mixed, temp_supply, rh_supply, m_coil, temp_coil, v_mixed_air, unit ):
    # mixed air psychrometrics
    
    cost_arr = []
    pw_arr = []
    for i in range(-24, 50):
        DBT = i + 273.15
        C8= -5.8002206*10**3
        C9= 1.3914993
        C10= -4.8640239*10**-2
        C11= 4.1764768*10**-5
        C12= -1.4452093*10**-8
        C13= 6.5459673
        P = 101325
        pw_mixed = m.exp(C8/DBT+C9+C10*DBT+C11*DBT**2+C12*DBT**3+C13*m.log(DBT)) 
        sh_mixed = (0.621945 * pw_mixed)/(P - pw_mixed)
        cost = 287.042 * DBT * (1+1.607858 * sh_mixed) / P
        cost_arr.append(cost)
        pw_arr.append(pw_mixed)
        
    P = 101325
    dbtemp_mixed = temp_mixed + 273.15
    
    pw_mixed = pw_arr[int(temp_mixed)+24] * (rh_mixed/100)
                
    sh_mixed = (0.621945 * pw_mixed)/(P - pw_mixed)    
    eth_mixed = 1.006 * temp_mixed + sh_mixed * (2501 + 1.86* temp_mixed)   
    sv_mixed = cost_arr[int(temp_mixed)+24]
    
    # supply air psychrometrics
    dbtemp_supply = temp_supply + 273.15
    
    pw_supply = pw_arr[int(temp_supply)+24] * (rh_supply/100)         
    sh_supply = (0.621945 * pw_supply)/(P - pw_supply)    
    eth_supply = 1.006 * temp_supply + sh_supply * (2501 + 1.86* temp_supply)   
    
    # condenser
    cp_water = 4.2
    temp_cond = temp_supply
    eth_cond = cp_water * temp_cond
    

    # cooling load calculation
    cooling_load = Real('cooling_load')
    m_air_mixed = Real('m_air_mixed')
    m_cond = Real('m_cond')
       
    s = Solver()
    s.add(m_air_mixed == v_mixed_air / sv_mixed)
    
    s.add( m_cond == m_air_mixed * (sh_mixed - sh_supply) )
    s.add( cooling_load ==  m_air_mixed * (eth_supply - eth_mixed) + m_cond * eth_cond )
    
    s.check()
    
    # loading cooling load cost (kW) into cost_coil
    coil_cost = float(Fraction(str(s.model()[cooling_load])))

    
    # chiller water input temperature = coil water output temperature
    temp_chil = temp_coil + (coil_cost / (m_coil * cp_water) ) 
    
    # chilling cost calculation (BTU/hr)
    chil_cost = m_coil * cp_water * (temp_chil - temp_coil) 
    
    
    total_cost = coil_cost + chil_cost
    #print("h",total_cost)
    #print('pw_mixed', pw_mixed)
    #print('pw_mixed', pw_supply)
    #print('eth_mixed', eth_mixed)
    #print('sv_mixed', sv_mixed)
    #print('sh_mixed', sh_mixed)
    #print('eth_supply', eth_mixed)
    #print('sh_supply', sh_supply)
    
    if unit == "BTU":
        return total_cost * 3412.142
    elif unit == "kWh":
        return total_cost        
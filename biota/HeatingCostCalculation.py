"""
Created on Wed Sep 30 14:54:37 2020
@author: haque
"""

import PSYSI
from z3 import *

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
# CP_WATER:       water heat capacity (kJ/kg.K)
    

############################### Coil ######################################
# m_coil:         cooling water mass flow rate in coil (kg/s)
# temp_coil:      cooling water inlet temperature in coil (degree C)
# spht_coil:      specific heat capacity of water in coil (kJ/kg.K)


########################### Chilling tower ################################
# temp_chil:      input temperature of chilling tower (degree C)


################################# Costs ###################################
# cooling_load:   cooling load (kW)
# chiller_load:   cooling load (kW)


def HeatingCostCalculation( temp_mixed, rh_mixed, temp_supply, rh_supply, m_coil, temp_coil, v_mixed_air, unit ):
    # mixed air psychrometrics
    psy_mixed = PSYSI.state("DBT", temp_mixed + 273 ,"RH", rh_mixed / 100, 101325)

    eth_mixed = psy_mixed[1] 
    sv_mixed  = psy_mixed[3]
    sh_mixed  = psy_mixed[4] 
    
    
    # supply air psychrometrics
    psy_supply = PSYSI.state("DBT", temp_supply + 273 ,"RH", rh_supply / 100, 101325)

    eth_supply = psy_supply[1] 
    sh_supply  = psy_supply[4] 
    
    # condenser
    CP_WATER = 4.2
    temp_cond = temp_supply
    eth_cond = CP_WATER * temp_cond
    

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
    temp_chil = temp_coil + (coil_cost / (m_coil * CP_WATER) ) 
    
    # chilling cost calculation (kWh)
    chil_cost = m_coil * CP_WATER * (temp_chil - temp_coil) 
    
    total_cost = coil_cost + chil_cost
    #print("c",total_cost)
# =============================================================================
#     print('eth_mixed', eth_mixed)
#     print('sv_mixed', sv_mixed)
#     print('sh_mixed', sh_mixed)
#     print('eth_supply', eth_mixed)
#     print('sh_supply', sh_supply)
# =============================================================================
    
    
    if unit == "BTU":
        return total_cost * 3412.142
    elif unit == "kWh":
        return total_cost
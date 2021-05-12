import pandas as pd
import numpy as np

from datetime import datetime  
from datetime import timedelta 


def DatasetGeneration(dataset_file, start_date, end_date):
    dataset = pd.read_csv(dataset_file)
    date = dataset.iloc[:,0]
    time = dataset.iloc[:,1]
    
    dataset_datetime = []
    
    
    for i in range(len(date)):
        month, day, year = [int(x) for x in date[i].split('/')]
        if year < 2000:
            year = year + 2000
        hour, minute, second = [int(x) for x in time[i].split(':')]
        dataset_datetime.append([datetime(year, month, day, hour, minute, second), dataset.iloc[i,2]])
    
    
    date_array = []
    
    
    curr_date = start_date
    
    while curr_date < end_date:
        curr_date = curr_date + timedelta(minutes = 10)
        date_array.append([curr_date, 0])
        
    index = 0
    
    for i in range(len(date_array)):
        if index == len(dataset_datetime)-1:
            break
        if (date_array[i][0] >= dataset_datetime[index][0]):
            vals = []
            while( date_array[i][0] >= dataset_datetime[index ][0] ) and index < len(dataset_datetime)-2:
                vals.append(dataset_datetime[index ][1])
                index+=1
            if len(vals) > 0:
                date_array[i][1] = round(sum(vals)/len(vals))
        else:       
            continue
    return np.asarray(date_array), max(np.asarray(date_array)[:,1])
    
    
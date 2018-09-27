# -*- coding: utf-8 -*-
"""
Created on Wed Aug  8 20:52:58 2018

@author: Magnus
""" 
import pandas as pd 
import numpy as np

class ColumnData():
    """
    Header should be "Kortnamn". 
    """
    def __init__(self, file_path, **kwargs): 
        
        self.file_path = file_path
        self.kwargs = kwargs
        
        # Loading file
        kw = {'sep':'\t',
              'encoding':'cp1252'}
        kw.update(self.kwargs)
        self.df = pd.read_csv(self.file_path, **kw)
        
        self.df['time_str'] = self.df['SDATE'] + ' ' + self.df['STIME'] 
        self.df['time'] = pd.to_datetime(self.df['time_str'], format='%Y-%m-%d %H:%M')
        
        self.df['station_id'] = self.df['STATN'] + ' <=> ' + self.df['time_str']

    
    #==========================================================================
    def get_filtered_data(self, **kwargs): 
        """
        Lists as value only possible if key in kwargs matches self.df.columns.  
        """
        boolean = ~self.df['DEPH'].isnull() 
        
        if kwargs.get('depth'):  
            boolean = boolean & (self.df['depth'] == kwargs['depth'])
            
        if kwargs.get('depth_interval'): 
            boolean = boolean & self.df['DEPH'].between(kwargs['depth_interval'][0], 
                                                        kwargs['depth_interval'][-1])
            
        if kwargs.get('station'):  
            boolean = boolean & (self.df['STATN'] == kwargs['station'])
            
        if kwargs.get('station_id'):  
            boolean = boolean & (self.df['station_id'] == kwargs['station_id']) 
            
        for col in self.df.columns:
            if kwargs.get(col): 
                value = kwargs.get(col) 
                if type(value) in [list, tuple]:
                    boolean = boolean & self.df[col].isin(value)
                else:
                    boolean = boolean & (self.df[col] == value)
            
        return self.df.loc[boolean, :].copy()
        
    
    #==========================================================================
    def get_profile(self, par, **kwargs):
        df = self.get_profile_df(**kwargs)
        if type(df) == bool and df == False:
            return False 
        else: 
            return df['DEPTH'], df[par]
        
        
    #==========================================================================
    def get_profile_df(self, **kwargs):
        df = self.get_filtered_data(**kwargs) 
        
#        return df
        if len(set(df['station_id'])) != 1:
            return False
        else: 
            columns = []
            for col in df.columns: 
                if kwargs.get('exclude_empty_profiles'):
                    if all(np.isnan(df[col])):
                        continue
                if col == 'DEPH':
                    columns.append(col)
                elif col.startswith('Q_'):
                    columns.append(col[2:])
                    if kwargs.get('include_qf'):
                        columns.append(col)
            return df[kwargs.get('include_columns', []) + columns]
    
    
    #==========================================================================
    def get_station_list(self):
        return sorted(set(self.df['STATN'])) 
    
    
    #==========================================================================
    def get_station_id_list(self):
        return sorted(set(self.df['station_id'])) 
    
    
    #==========================================================================
    def get_time_series(self, par, **kwargs): 
        
        df = self.get_filtered_data(**kwargs) 
        
        groups = df.groupby('time')
        
        time_list = [] 
        value_list = []
        for g in groups: 
            time_list.append(g[0]) 
            depths = g[1]['DEPH']
            values = g[1][par] 
            value_list.append(self._calc_integrated_mean(depths, values, **kwargs))
        
        return time_list, value_list 
    
        
    #==========================================================================
    def _calc_integrated_mean(self, depths, values, **kwargs):
        if kwargs.get('depth_interval'):
            from_depth, to_depth = kwargs['depth_interval']
        elif kwargs.get('depth'):
            from_depth = to_depth = kwargs['depth']
        else:
            from_depth = kwargs.get('from_depth', self.df['DEPH'].min())
            to_depth = kwargs.get('to_depth', self.df['DEPH'].max())
        
        depth_list = []
        value_list = []
        for d, v in zip(depths, values):
            if not np.isnan(v) and (d >= from_depth) and (d <= to_depth):
                depth_list.append(d)
                value_list.append(v)
        
        if not depth_list:
            return np.nan
        
        if depth_list[0] > from_depth:
            depth_list.insert(0, from_depth)
            value_list.insert(0, value_list[0])
        if depth_list[-1] < to_depth:
            depth_list.append(to_depth)
            value_list.append(value_list[-1])
        
        integrated = []
        for d0, d1, v0, v1 in zip(depth_list[:-1], depth_list[1:], value_list[:-1], value_list[1:]): 
            cal = (d1-d0)*(v1+v0)/2
            integrated.append(cal)
        integrated_mean = np.nansum(integrated)/(depth_list[-1]-depth_list[0])

        return integrated_mean
    
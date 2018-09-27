# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 18:38:28 2018

@author: Magnus
"""
import os 
import pandas as pd

class SynonymDict(dict):
    """
    SynonymDict mapp all columns in the given file. For each column the first 
    row is the prefered label. All other rows in the column are synonyms and will
    become a key in self. The values for each key will be the first row. 
    Class uses pandas to read files. 
    default separator is tab and encoding is cp1252
    """
    def __init__(self, 
                 file_path, 
                 include_as_is=True, 
                 include_lowercase=False, 
                 include_uppercase=False, 
                 **kwargs):
        
        if not os.path.exists(file_path):
            raise FileNotFoundError
        
        self.file_path = file_path
        self.ending = file_path.split('.')[-1]
        self.include_as_is = include_as_is
        self.include_lowercase = include_lowercase
        self.include_uppercase = include_uppercase
        
        self.kwargs = kwargs
        
        # Loading file
        if self.ending == 'xlsx':
            df = pd.read_excel(self.file_path, **self.kwargs)
        
        else:
            kw = {'sep':'\t',
                  'encoding':'cp1252'}
            kw.update(self.kwargs)
            df = pd.read_csv(self.file_path, **kw)
            
        df.fillna('', inplace=True)  
        
        for col in df.columns:
            for key in df[col].values:
                if key: 
                    if self.include_as_is:
                        self[key] = col
                    if self.include_lowercase:
                        self[key.lower()] = col
                    if self.include_uppercase:
                        self[key.upper()] = col
                    
    
    
class MappingDict():
    """
    MappingDict is used to mapp items in the same row between different columns. 
    Items are strings. 
    """
    def __init__(self, 
                 file_path,
                 **kwargs): 
        
        if not os.path.exists(file_path):
            raise FileNotFoundError 
            
        self.file_path = file_path
        self.ending = file_path.split('.')[-1]
        
        self.kwargs = kwargs
        
        # Loading file
        if self.ending == 'xlsx':
            self.df = pd.read_excel(self.file_path, **self.kwargs)
        
        else:
            kw = {'sep':'\t',
                  'encoding':'cp1252'}
            kw.update(self.kwargs)
            self.df = pd.read_csv(self.file_path, **kw)
    
        self.df.fillna('', inplace=True)  
        
    
    #==========================================================================
    def __call__(self, item, from_col=False, to_col=False, **kwargs):
        """
        By default item is returned if no match. "blank_if_missning" can be set to True 
        during initiation of object or in kwargs in the method call. 
        """
        if not from_col:
            from_col = self.kwargs.get('from_col', False) 
        if not to_col:
            to_col = self.kwargs.get('to_col', False) 
        
        if not all([from_col, to_col]):
            raise ValueError 
            
        if not from_col in self.df.columns:
            raise ValueError 
            
        if not to_col in self.df.columns:
            raise ValueError 
        
        result = list(self.df.loc[self.df[from_col]==item, to_col])
        if result:
            return result[0]
        else: 
            kw = self.kwargs.copy()
            kw.update(kwargs)
            if kw.get('blank_if_missing'):
                return '' 
            elif kw.get('missing_value'):
                return kw.get('missing_value')
            else:
                return item
    
    
    
    
    
    
    
    
    
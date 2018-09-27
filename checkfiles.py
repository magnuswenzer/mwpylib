# -*- coding: utf-8 -*-
"""
Created on Sun Jul 22 12:55:23 2018

@author: Magnus
"""
import os
from pathlib import Path 
import pandas as pd 
import numpy as np
import datetime 

class Explore():
    """
    Class to explore directories. 
    """
    def __init__(self, directory):
        self.directory = directory
        self.root = Path(self.directory) 
        self._display_line_length = 90
        
#        self.columns = ['path', 'parent_directory', 'parent_folder', 'name', 'suffix', 'size', 'TYPE']
        self.columns = ['path', 'parent_directory', 'name', 'suffix', 'size', 'TYPE']
        
        self._load_walk()
        
    
    #==========================================================================
    def _get_info_tuple_for_path(self, path): 
        """
        Returns a tuple corsponding to to the items in self.columns
        """
        stat = os.stat(str(path))
        if path.is_dir():
            t = 'directory'
            name = os.path.basename(str(path))
        else:
            t = 'file'
            name = path.name
            
#        parent_folder = os.path.basename(str(path.parent))
#        data = (path, str(path.parent), parent_folder, name, path.suffix[1:], stat.st_size, t)
        
        data = (path, str(path.parent), name, path.suffix[1:], stat.st_size, t)
        
        return data
    
    
    #==========================================================================
    def _load_walk(self): 
        """
        Stores data in self.df. Columns are set to items in self.columns. 
        """
        
        path_list = []
        # parts_list = []
        for k, (root, dirs, files) in enumerate(os.walk(self.directory, topdown=True)):
            for name in files:
                path = Path(os.path.join(root, name))
                try:
                    path_list.append(self._get_info_tuple_for_path(path))
                except:
                    print(path)
            for name in dirs:
                path = Path(os.path.join(root, name))
                try: 
                    path_list.append(self._get_info_tuple_for_path(path))
                except:
                    print(path)
        
        self.df = pd.DataFrame(data=path_list, columns=self.columns) 
        
        self._add_directory_size()
        
    
    #==========================================================================
    def _add_directory_size(self):
        """
        Calculated the directory size for each directory. 
        Does this in reverce order (of the df) to include size of subdirectories. 
        """
        index = reversed(self.df.loc[self.df['TYPE']=='directory', :].index)
        for i in index: 
            full_path = str(self.df.loc[i, 'path'])
            directory_size = self.df.loc[self.df['parent_directory'] == full_path, 'size'].sum()
#            print(directory_size)
            self.df.loc[i, 'size'] = directory_size
#            break
#        self.df.loc[self.df['TYPE']=='directory', 'size'] = np.nan 

    
    #==========================================================================
    def _get_filtered_dataframe(self, **kwargs): 
        """
        Returns a filtered dataframe that matches the criteria in kwargs. 
        key is the columns and values is the item to match in column. 
        """
        boolean = ~self.df['path'].isnull()
        for key, value in kwargs.items(): 
            boolean = boolean & self.df.loc[self.df[key] == value, :]            
        return self.df.loc[boolean, :]
        
    
    #==========================================================================
    def _convert_size(self, value, **kwargs):
        """
        Convert value from bytes to the the key in kwargs. 
        value can be number or list of numbers.  
        Current possoble conversions are: 
            kb
            Mb
        If no key in kwargs int(value) is returned 
        """
        def _convert(v): 
            if kwargs.get('unit', '') == 'kb':
                return int(v/1e3)
            elif kwargs.get('unit', '') == 'Mb':
                return v/1e6
            else:
                return int(v)
        
        if type(value) == list:
            out_list = []
            for item in value: 
                out_list.append(_convert(item))
            return out_list
        else:
            return _convert(value)
    
    
    #==========================================================================
    def _get_filtered_data(self, **kwargs): 
        boolean = ~self.df['name'].isnull()
        if kwargs.get('only_files'): 
            boolean = boolean & (self.df['TYPE'] == 'file')
            
        if kwargs.get('file_formats'): 
            b = self.df['name'].isnull()
            file_formats = kwargs.get('file_formats')
            if type(file_formats) == str:
                file_formats = [file_formats]
            for file_type in file_formats:
                b = b | (self.df['suffix'] == file_type) 
            boolean = boolean & b 
            
        return self.df.loc[boolean, :].copy()
    
    
    #==========================================================================
    def list_files(self, *args, **kwargs): 
        """
        List the files in the directory. 
        Several options in kwargs. 
        returns a pandas dataframe with matching data. 
        """
        kw = {'only_files': True, 
              'sort_by': 'size'}
        kw.update(kwargs) 
        
        df = self._get_filtered_data(**kw)
        
        if kw['sort_by'] == 'size':
            df.sort_values('size', ascending=False, inplace=True) 
        else: 
            df.sort_values(kw['sort_by'], ascending=True, inplace=True)
            
        return df[['name', 'size', 'parent_directory']] 
    
    
    #==========================================================================
    def print_file_information(self, *args, **kwargs):
        df = self.list_files(*args, **kwargs) 
        
        kw = {'unit': 'kb'}
        kw.update(kwargs) 
        
        col_1 = 50
        col_2 = 20
        
        print('='*self._display_line_length) 
        print('{}{}{}'.format('Filnamn'.ljust(col_1), 'Filstorlek ({})'.format(kw['unit']).ljust(col_2), 'Mapp'))
        print('-'*self._display_line_length)
        for i in df.index:
            name = str(df.loc[i, 'name'])
            s = str(self._convert_size(df.loc[i, 'size'], **kw))
            parent_directory = str(df.loc[i, 'parent_directory'])
            print('{}{}{}'.format(name.ljust(col_1), s.ljust(col_2), parent_directory))
        print('-'*self._display_line_length)
        
    
    #==========================================================================
    def get_subdirectory_object(self, directory): 
        if directory not in self.df['name'].values:
            return False
        return Explore(str(self.df.loc[self.df['name']==directory, 'path'].values[0]))
                
    
    #==========================================================================
    def save_information(self, file_path, *args, **kwargs):
        df = self._get_filtered_data(**kwargs) 
        
        df['size'] = df['size'].apply(lambda x: self._convert_size(x, **kwargs)) 
        
        df['source'] = kwargs.get('source_column', df['parent_directory'].str[0]) 
        
#        print(len(df))
        if os.path.exists(file_path):
            temp_df = pd.read_excel(file_path, encoding='cp1252') 
#                print('temp_df', len(temp_df))
            df = df.append(temp_df) 
#                print(len(df))
                
        df['path'] = df['path'].apply(str)
#        temp_df['path'] = temp_df['path'].apply(str)
        
        df.drop_duplicates('path', inplace=True) 
#        print(len(df))
        if kwargs.get('sort'): 
            df.sort_values('name', inplace=True) 
            
#        print(df.head())
#        print(df['path'].values[0] == df['path'].values[1])
         
        
        df.to_excel(file_path, index=False, encoding='cp1252')
        
    
    
    
    
    
    
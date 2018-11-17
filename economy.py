# -*- coding: utf-8 -*-
"""
Created on Thu Jul  5 08:14:07 2018

@author: Magnus
""" 
import os 
import sys 
import numpy as np 
import pandas as pd 
import datetime 


mw_lib_path = os.path.dirname(os.path.abspath(__file__))
if mw_lib_path not in sys.path:
    sys.path.append(mw_lib_path) 

from html_plot import PlotlyPlot

class Nordea():
    """
    Created 20180705 
    """
    def __init__(self,
                 source_directory='', 
                 kategori_mapping_file=''):
        
        self.source_directory = source_directory 
        self.kategori_mapping_file = kategori_mapping_file 
        
        self._display_line_length = 90
        
        self._load_files() 
        
        
    #==========================================================================
    def _get_month(self, month=None):
        if not month:
            month = datetime.datetime.now().month
        return month
    
    
    #==========================================================================
    def _get_year(self, year=None):
        if not year:
            year = datetime.datetime.now().year
        return year
    
    
    #==========================================================================
    def _get_boolean(self, key, value): 
        if type(value) not in [list, tuple]: 
            return self.df[key] == value 
        else:
            return self.df[key].isin(value) 
        
    #==========================================================================
    def _get_df_from_args_and_kwargs(self, *args, **kwargs): 
        """
        Creates a boolean based on selection. 
        args can be: 
            int <= 12       = month
            int >= 2000     = year 
        """
        # Add positive years and months
        month_list = []
        year_list = []
        for a in args: 
            if type(a) == int and a > 0:
                if a <= 12:
                    month_list.append(a) 
                elif a >= 2000: 
                    year_list.append(a) 
                    
        # All years and month if none given
        if not month_list:
            month_list = list(set(self.df['month']))
        if not year_list:
            year_list = list(set(self.df['year'])) 
           
        # Remove negative years and months
        for a in args: 
            if type(a) == int and a < 0:
                if a >= -12:
                    if -a in month_list:
                        month_list.remove(-a) 
                elif a >= -2000: 
                    if -a in month_list:
                        year_list.remove(-a) 
                        
        # Check category
        cat_list = [] 
        not_cat_list = []
        sub_cat_list = [] 
        not_sub_cat_list = []
        for a in args: 
            if type(a) != str:
                continue
            if a in self.df['Kategori'].values: 
                cat_list.append(a)
            elif a[0]=='-'and a[1:] in self.df['Kategori'].values:
                # print('NOT IN KATEGORI')
                not_cat_list.append(a[1:])
            elif a in self.df['Underkategori'].values: 
                sub_cat_list.append(a)
            elif a[0]=='-'and a[1:] in self.df['Underkategori'].values: 
                not_sub_cat_list.append(a[1:])
        
        kwargs['kategori'] = cat_list + kwargs.get('kategori', [])
        kwargs['ej_kategori'] = not_cat_list + kwargs.get('ej_kategori', [])
        
        kwargs['underkategori'] = sub_cat_list + kwargs.get('underkategori', [])
        kwargs['ej_underkategori'] = not_sub_cat_list + kwargs.get('ej_underkategori', [])
                    
                    
        
        # Create boolean 
        boolean = self._get_true_boolean()
#        print(len(np.where(boolean)[0]))
        boolean = boolean & self._get_year_boolean(year_list)
#        print(len(np.where(boolean)[0]))
        boolean = boolean & self._get_month_boolean(month_list)
#        print(len(np.where(boolean)[0]))
#         print("kwargs['ej_kategori']", kwargs['ej_kategori'])
        boolean = boolean & self._get_exclude_boolean(**{'Kategori': kwargs.get('ej_kategori')})
        # print(len(np.where(~boolean)[0]), np.where(~boolean))
#        print(len(np.where(boolean)[0]))
        boolean = boolean & self._get_include_boolean(**{'Kategori': kwargs.get('kategori')})
        # print(len(np.where(~boolean)[0]), np.where(~boolean))
#        print(len(np.where(boolean)[0])) 
        boolean = boolean & self._get_exclude_boolean(**{'Underkategori': kwargs.get('ej_underkategori')})
        boolean = boolean & self._get_include_boolean(**{'Underkategori': kwargs.get('underkategori')})
        
        return self.df.loc[boolean, :].copy()
    
        
    #==========================================================================
    def _get_exclude_boolean(self, **kwargs): 
        """
        Returns a boolean that excludes the items in kwargs. 
        Boolean is True for all lines that are not excluded. 
        """
        boolean = ~self._get_true_boolean()
        for key, value in kwargs.items():
            if not value:
                continue
            boolean = boolean | self._get_boolean(key, value)
        return ~boolean
    
    
    #==========================================================================
    def _get_include_boolean(self, **kwargs): 
        """
        Returns a boolean that includes the items in kwargs. 
        Boolean is True for all lines that are included. 
        """
         
        added = False
        boolean = ~self._get_true_boolean()
        for key, value in kwargs.items():
            if not value:
                continue
            boolean = boolean | self._get_boolean(key, value)
            added = True 
        
        if not added:
            return self._get_true_boolean()
        else:
            return boolean
            
        
    #==========================================================================
    def _get_month_boolean(self, month): 
        month = self._get_month(month)
        if type(month) == int: 
            return self.df['month'] == month 
        else:
            return self.df['month'].isin(month) 
        
    
    #==========================================================================
    def _get_true_boolean(self):
        return ~self.df['Belopp'].isnull()
        
        
    #==========================================================================
    def _get_year_boolean(self, year): 
        year = self._get_year()
        if type(year) == int: 
            return self.df['year'] == year 
        else:
            return self.df['year'].isin(year)
    
    #==========================================================================
    def _get_kategori_boolean(self, kategori):
        return self.df['Kategori'] == kategori
    
    
    #==========================================================================
    def _get_underkategori_boolean(self, underkategori):
        return self.df['Underkategori'] == underkategori
    
    
    #==========================================================================
    def _convert_float(self, x):
        if type(x) == str: 
            return -float(x.replace('.', '').replace(',', '.'))
        else:
            return x
    
    
    #==========================================================================
    def _load_files(self):
        self.df = ()
        for file_name in os.listdir(self.source_directory):
            if not file_name.endswith('xls'):
                continue 
            file_path = os.path.join(self.source_directory, file_name)
#            print('file_path', file_path)
            temp_df = pd.read_excel(file_path) 
            if not len(self.df):
                self.df = temp_df
            else:
                self.df = self.df.append(temp_df) 

        self.df['Kategori'] = ''
        self.df.fillna('', inplace=True) 
        
        # Ta bort dubletter
        self.df.drop_duplicates(inplace=True)
        
        # Fixa datum och månad
        self.df['Datum'] = pd.to_datetime(self.df['Datum']) 
        self.df['month'] = self.df['Datum'].dt.month
        self.df['year'] = self.df['Datum'].dt.year 
        self.df['year_month'] = self.df['year'].astype(str) + '_' + self.df['month'].astype(str)
        
        # Convert to float
        float_columns = ['Belopp']
        for col in float_columns:
            self.df[col] = self.df[col].apply(self._convert_float)
            
        # Lägg till kategori 
        mdf = pd.read_excel(self.kategori_mapping_file) 
        mdf.fillna('', inplace=True)
        for col in mdf.columns:
            for item in mdf[col]: 
        #         print(item, type(item))
        #         break
        #         print(item, col)
                if item:
                    self.df.loc[self.df['Transaktion'].str.contains(item), 'Kategori'] = col 
                    self.df.loc[self.df['Transaktion'].str.contains(item), 'Underkategori'] = item 
                    
        self.df.sort_values('Datum', inplace=True)
        self.df.reset_index(inplace=True)
        # print('resetting')
            
    
    #==========================================================================
    def get_non_categorized(self, save_to_file=True): 
        
        # Check file path
        file_path = False
        if os.path.isfile(save_to_file):
            file_path = save_to_file 
        elif save_to_file:
            file_path = os.path.join(self.source_directory, 'saknar_kategori.txt')
        
        no_kategory_list = self.df.loc[self.df['Kategori']=='', ['Datum', 'Belopp', 'Transaktion']].sort_values('Transaktion')
        
        if file_path:
            no_kategory_list.to_csv(file_path, sep='\t', encoding='cp1252', index=False)
#            with codecs.open(file_path, 'w',encoding='cp1252') as fid:
#                fid.write('\n'.join(no_kategory_list))
        if not len(no_kategory_list):
            print('All transaktioner är kategoriserade!')
            
        return no_kategory_list

    def plot_account_cumsum(self, *args, **kwargs):
        data = self._get_df_from_args_and_kwargs(*args, **kwargs)
        df_tot = data[['Datum', 'Belopp']]
        df_in = data.loc[data['Belopp'] < 0, ['Datum', 'Belopp']]
        df_out = data.loc[data['Belopp'] > 0, ['Datum', 'Belopp']]
        p = PlotlyPlot(title='Utveckling konto (cumsum)',
                       xaxis_title='Tidpunkt',
                       yaxis_title='kr på kontot')

        p.add_scatter_data(df_tot['Datum'], df_tot['Belopp'].cumsum()*-1, name='Totalt')
        p.add_scatter_data(df_in['Datum'], df_in['Belopp'].cumsum()*-1, name='Insättningar')
        p.add_scatter_data(df_out['Datum'], df_out['Belopp'].cumsum(), name='Utgifter')

        if kwargs.get('save_to_file'):
            p.plot_to_file(kwargs.get('save_to_file'))
        if kwargs.get('plot_in_notebook'):
            p.plot_in_notebook()

        return data

        #==========================================================================
    def plot_post(self, *args, **kwargs): 
        """
        Plots one or several post in args. Post can be category or subcategory. 
        """ 
#        all_df = self._get_df_from_args_and_kwargs(*args, **kwargs) 
        
        data = self._get_time_data_for_category(*args, **kwargs) 
        
        p = PlotlyPlot(title='Köp - kategori/underkategori', 
                           xaxis_title='Tidpunkt', 
                           yaxis_title='kr') 


        for cat in sorted(data): 
            if cat in self.df['Kategori'].values:
                name = '{} (Kategori)'.format(cat)
            else:
                name = '{} (Underkategori)'.format(cat)
                
            if kwargs.get('scatter'): 
                p.add_scatter_data(data[cat]['time'], 
                                   data[cat]['value'], 
                                   name=name)
            else: 
                p.add_bar_data(data[cat]['time'], 
                               data[cat]['value'], 
                               name=name)
        
        
#        for post in args: 
#            if post in all_df['Kategori'].values: 
#                df= all_df.loc[all_df['Kategori']==post, :] 
#                
#            elif post in all_df['Underkategori'].values:
#                df = all_df.loc[df['Underkategori']==post, :] 
#            else:
#                pass
#            
#            x_values = df['Datum']
#            y_values = df['Belopp']
#            
#            if kwargs.get('scatter'): 
#                p.add_scatter_data(x_values, y_values, name=post)
#            else: 
#                p.add_bar_data(x_values, y_values, name=post)
            
        
        if kwargs.get('save_to_file'): 
            p.plot_to_file(kwargs.get('save_to_file'))
        if kwargs.get('plot_in_notebook'):
            p.plot_in_notebook() 
        
        return data
        
    #==========================================================================
    def plot_summary(self, *args, **kwargs): 
        """
        Plots a summary based on selection. 
        agrs can be: 
            int <= 12      = month
            int >= 2000    = year 
        """
        if kwargs.get('pie'):
            if kwargs.get('by_month'): 
                # One pie chart for each month 
                data = self._get_category_data_by_month(*args, **kwargs) 
                
                p = PlotlyPlot(title='Jämförelse - Månad', 
                           xaxis_title='Månad', 
                           yaxis_title='kr') 
                
                r = 1 
                c = 1 
                nr_cols = 4
                nr_rows = len(data)//nr_cols + 1
                for k, cat in enumerate(sorted(data)): 
                    if k and not k%nr_cols:
                        r+=1
                        c=1
                    pos = '{}{}{}{}'.format(nr_cols, nr_rows, c, r)
#                    print(pos, cat)
                    p.add_pie_data(data[cat]['category'], 
                                   data[cat]['value'], 
                                   pos=pos, 
                                   name='{} Totalt: {} kr'.format(cat, int(np.nansum(data[cat]['value']))))
                    c+=1
            
            
            #------------------------------------------------------------------
            elif kwargs.get('by_category'): 
                # One pie chart for each month 
                data = self._get_month_data_by_category(*args, **kwargs) 
                
                p = PlotlyPlot(title='Jämförelse - Kategori', 
                           xaxis_title='Kategori', 
                           yaxis_title='kr') 
                r = 1 
                c = 1 
                nr_cols = 4
                nr_rows = len(data)//nr_cols + 1
                for k, cat in enumerate(sorted(data)): 
                    if k and not k%nr_cols:
                        r+=1
                        c=1
                    pos = '{}{}{}{}'.format(nr_cols, nr_rows, c, r)
#                    print(pos, cat)
                    p.add_pie_data(data[cat]['year_month'], 
                                   data[cat]['value'], 
                                   pos=pos, 
                                   name='{} Totalt: {} kr'.format(cat, int(np.nansum(data[cat]['value']))))
                    c+=1
        
        else: 
            if kwargs.get('by_month'):  
                data = self._get_month_data_by_category(*args, **kwargs) 
                
                p = PlotlyPlot(title='Jämförelse - Månad', 
                           xaxis_title='Månad', 
                           yaxis_title='kr')  
                
                for ym in sorted(data):
                    p.add_bar_data(data[ym]['year_month'], 
                                   data[ym]['value'],  
                                   name=ym, 
                                   barmode=kwargs.get('barmode', 'stack'))
                    

            elif kwargs.get('by_category'): 
                data = self._get_category_data_by_month(*args, **kwargs) 
                
                p = PlotlyPlot(title='Jämförelse - Kategori', 
                           xaxis_title='Kategori', 
                           yaxis_title='kr') 
                
                for cat in sorted(data):
                    p.add_bar_data(data[cat]['category'], 
                                   data[cat]['value'],  
                                   name=cat, 
                                   barmode=kwargs.get('barmode', 'stack'))
            
            
            

        if kwargs.get('save_to_file'): 
            p.plot_to_file(kwargs.get('save_to_file'))
        if kwargs.get('plot_in_notebook'):
            p.plot_in_notebook()  

      
    
    #==========================================================================
    def _get_month_data_by_category(self, *args, **kwargs): 
        
        df = self._get_df_from_args_and_kwargs(*args, **kwargs)
        
        all_ym_list = [x.replace('_', ':') for x in sorted(set(df['year_month']))]
        data = {}
        for category in sorted(set(df['Kategori'])): 
            category_df = df.loc[df['Kategori']==category, :]
            group = category_df.groupby('year_month').sum().reset_index() 
            ym_list = group['year_month'].values
            ym_list = [x.replace('_', ':') for x in ym_list]
            value_list = group['Belopp'].values 
            # Extend value list 
            value_list = [value if ym in ym_list else np.nan for value, ym in zip(value_list, all_ym_list)]
            data[category] = dict(year_month=all_ym_list, 
                                  value=value_list)
        return data 
            
    
    #==========================================================================
    def _get_category_data_by_month(self, *args, **kwargs): 
        
        df = self._get_df_from_args_and_kwargs(*args, **kwargs)
        
        all_category_list = sorted(set(df['Kategori']))
        data = {}
        for ym in set(df['year_month']): 
#                print(ym)
            ym_df = df.loc[df['year_month']==ym, :]
            group = ym_df.groupby('Kategori').sum().reset_index() 
            category_list = group['Kategori'].values 
#            print(category_list)
            value_list = group['Belopp'].values 
            # Extend value list
            extended_value_list = []
            for c in all_category_list: 
                if c in category_list: 
                    index = list(category_list).index(c)
                    extended_value_list.append(value_list[index])
                else:
                    extended_value_list.append(np.nan)
#            value_list = [value if c in category_list else np.nan for value, c in zip(value_list, all_category_list)]
            
            data[ym] = dict(category=all_category_list, 
                            value=extended_value_list)
    
        return data 
            
    
    #==========================================================================
    def _get_time_data_for_category(self, *args, **kwargs): 
        """
        Returns a time series for a category or subcategory. 
        If several posts the same day. The sum is given.
        """
        
        df = self._get_df_from_args_and_kwargs(*args, **kwargs)
        
        data = {}
        for cat in set(df['Kategori']): 
            if cat not in args:
                continue
            cat_df = df.loc[df['Kategori']==cat, :]
            group = cat_df.groupby('Datum').sum().reset_index() 
            time_list = [str(item).replace('T', ' ') for item in group['Datum'].values] 
            value_list = group['Belopp'].values
            data[cat] = dict(time=time_list, 
                             value=value_list)
            
        for subcat in set(df['Underkategori']): 
            if subcat not in args:
                continue
            subcat_df = df.loc[df['Underkategori']==subcat, :]
            group = subcat_df.groupby('Datum').sum().reset_index() 
            time_list = [str(item).replace('T', ' ') for item in group['Datum'].values] 
            value_list = group['Belopp'].values 
            data[subcat] = dict(time=time_list, 
                             value=value_list)
            
        return data 
        
         
    #==========================================================================
    def get_categories(self):
        return sorted(self.df['Kategori'].unique())
        
    
    #==========================================================================
    def get_subcategories(self, category, **kwargs): 
        boolean = self._get_true_boolean()
        if kwargs.get('year'): 
            boolean = boolean & self._get_year_boolean(kwargs['year'])
        if kwargs.get('month'):
            boolean = boolean & self._get_month_boolean(kwargs['month'])
        
        if category: 
            boolean = boolean & (self.df['Kategori']==category)

        df = self.df.loc[boolean, :]
        return sorted(df['Underkategori'].unique())
    
        
    #==========================================================================
    def print_categories(self, *args, **kwargs):
        print('\n'.join(self.get_categories()))
    
    
    #==========================================================================
    def print_subcategories(self, *args, **kwargs):
        print('\n'.join(self.get_subcategories(*args, **kwargs)))
        
              
    #==========================================================================
    def print_non_categorized(self): 
        non_categorized = sorted(self.get_non_categorized()['Transaktion'])
        print('\n'.join(non_categorized))
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
            
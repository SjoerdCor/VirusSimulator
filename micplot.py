# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 07:48:14 2019

@author: Gebruiker
"""
import matplotlib.pyplot as plt
import pandas as pd
import math
import seaborn as sns

pd.options.plotting.backend = 'matplotlib'
HIGHLIGHT_COLOR = 'purple' # Standard in my organization, but you can customize this

def plot_values_above_bar(data, display_values=None, ax=None, strfmt='.2f', orient='v',
                          textcolor='black', bar_nr=None, nr_bars=None):
    '''
    Helper function to display values above (or on) bar plot)
    
    Parameters
    ----------
    data: the series containing the position of the labels
    display_values: Optionally: the values to display if different from data
    ax: Axis object on which the labels should be plotted
    strfmt: the format-string for the labels
    orient: "v"(ertical) bars or "h"(orizontal) bars
    bar_nr: if the plot contains multiple bar charts, which of the series we want to label
    nr_bars: if the plot contains multiple bar charts, how many series are shown in total
    '''
    if (bar_nr is None) != (nr_bars is None):
        raise ValueError('Either both bar_nr and nr_bars should be None, or neither')
    
    display_values = data if display_values is None else display_values
    if ax is None:
        ax = plt.gca()
    
    if orient == 'v':
        lim_min, lim_max = ax.get_xlim()
        va = 'center'
        ha = 'left'
    elif orient == 'h':
        lim_min, lim_max = ax.get_ylim()
        va = 'bottom'
        ha = 'center'
    else:
        raise ValueError(f'orient must be "v" or "h", not {orient}')
    plotsize = lim_max - lim_min 
    
    for i, (v, dv) in enumerate(zip(data, display_values)):
        v += 0.025 * plotsize # offset label little bit
        if nr_bars is not None:
            i += -0.5 + 1/(nr_bars+2) * (bar_nr + 1)
        
        x = v if orient == 'v' else i
        y = i if orient == 'v' else v
        label = '{:{prec}}'.format(dv, prec=strfmt)
        ax.text(x, y, label, color=textcolor, va=va, ha=ha)
    

def plot_waterfall(data, color=None, buildup=False, **kwargs):
    '''
    Plot a buildup or builddown waterfall chart from data
    
    Parameters
    ----------
    data: pd.Series to be shown as waterfall
    color: optionally give color as a list for each bar (to highlight some bars)
    buildup: False (default) for builddown, True for buildup
    
    Returns
    -------
    ax: Axis object
    data: the data, including a "total"-row
    blank: the size of the blank space before each bar
    '''
    if color is None:
        color = ['lightgray'] * len(data)

    # taken from https://pbpython.com/waterfall-chart.html
    blank = data.cumsum().shift(1).fillna(0)
    total = data.sum()
    data.loc['total'] = total
    blank.loc['total'] = 0
    color = color + ['gray']
    
    if buildup:
        data = data[::-1]
        blank = blank[::-1]
        color = color[::-1]
    
    ax = data.plot(kind='barh', stacked=True, left=blank, color=color, **kwargs)
    return ax, data, blank

def define_colors(highlight, data, plottype):
    '''
    Returns a list of colors with appropiate highlights
    
    Parameters
    ----------
    highlight: integer index or list of indices of rows which should be highlighted
    data: the series or dataframe for which the colors are calculated
    plottype: string of which plottype to use
    
    Returns
    -------
    color: list of len(data) with colors and appropriate highlights
    '''
    if isinstance(data, pd.Series) or plottype == 'scatter':
        color = ['lightgray'] * len(data)
    elif isinstance(data, pd.DataFrame):
        color = ['lightgray'] * data.shape[1]
    else:
        raise TypeError('data should be of type DataFrame or Series')
    try:
        for h in highlight:
            if h < 0: 
                h = len(data) + h
            color[h] = HIGHLIGHT_COLOR
    except TypeError:
        color[highlight] = HIGHLIGHT_COLOR
    return color

def is_percentage_series(series):
    '''
    Checks whether a series contains all percentages
    
    By checking whether all values are between 0 and 1, and the sum is equal to 1
    '''
    return series.between(0, 1).all() and math.isclose(series.sum(), 1)

def pick_plottype(data):
    '''
    Determines plottype base on shape and content of data
    Based on MIcompany training
    
    Parameters
    ----------
    data: pandas Series or DataFrame
    
    Returns
    -------
    plottype: string of plottype to be used by micompanyify
    '''
    if isinstance(data.index, pd.DatetimeIndex):
        if len(data) < 10:
            plottype = 'bar_timeseries'
        else:
            plottype = 'line_timeseries'
    elif isinstance(data, pd.Series):
        if is_percentage_series(data):
            plottype = 'waterfall'
        else:
            plottype = 'bar'
    elif isinstance(data, pd.DataFrame):
        if data.apply(is_percentage_series).all():
            plottype = 'composition_comparison'
        else:
            plottype = 'scatter'
    return plottype


def micompanyify(data, highlight=-1, plottype=None, ascending=True, strfmt=None, **kwargs):
    '''
    Nicer visualization for basic plot, returning the axis object
    Automatically chooses plot type and nicely makes up the plot area based on learnings from
    the MIcompany training
    
    Parameters
    ----------
    data: must be a pandas.Series or pandas.DataFrame 
    highlight: the index or list of indices of the data point you want to highlight
    plottype: inferred from the data, but can be overridden:
        'bar' (horizontal bar), 'bar_timeseries' (vertical bars), 'line_timeseries',
        'waterfall' (builddown), 'waterfall_buildup', 'composition_comparison' or 'scatter'
    ascending: sorting direction. By default largest values are shown at the 
                top, but False is possible, or None to leave the sorting as is
    strfmt: how to format accompanying data labels above bars, e.g. ".2f" or ".1%"
    **kwargs: will be passed to pd.Dataframe.plot()
    
    Returns
    -------
    :class:`matplotlib.axes.Axes` object with the plot on it

    
    '''
    if not isinstance(data, pd.DataFrame) and not isinstance(data, pd.Series):
        raise TypeError(f'Data is not of type Series or DataFrame, but type {type(data)}')

    data = data.squeeze() # DataFrame with single column should be treated as Series
    
    if plottype is None:
        plottype = pick_plottype(data)
         
    orient = 'h' if plottype in ['bar_timeseries', 'line_timeseries'] else 'v'
    
    if strfmt is None:
        if (isinstance(data, pd.DataFrame) and data.apply(is_percentage_series).all()) or\
        (isinstance(data, pd.Series) and is_percentage_series(data)):
            strfmt = '.1%'
        else:
            strfmt = '.2f'
    
    color = define_colors(highlight, data, plottype)
    
    if plottype in ['scatter', 'piechart', 'composition_comparison', 'bar_timeseries',
                    'line_timeseries'] or not isinstance(data, pd.Series):
        ascending = None
    
    if ascending is not None:
        data = data.sort_values(ascending=ascending)   
    
    if plottype == 'bar':
        ax = data.plot(kind='barh', color=color, **kwargs)
        if isinstance(data, pd.Series):
            plot_values_above_bar(data, orient=orient, strfmt=strfmt)
        else:
            for i, col in enumerate(data.columns):
                plot_values_above_bar(data[col], orient=orient, strfmt=strfmt,
                                      bar_nr=i, nr_bars=len(data.columns))
        
    elif plottype == 'waterfall':
        ax, data, blank = plot_waterfall(data, color=color, **kwargs)
        plot_values_above_bar((data+blank), data, ax=ax, strfmt=strfmt, orient=orient)
    elif plottype == 'waterfall_buildup':
        ax, data, blank = plot_waterfall(data, color=color, buildup=True, **kwargs)
        if pd.options.plotting.backend == 'matplotlib':
            plot_values_above_bar((data+blank), data, ax=ax, strfmt=strfmt, orient=orient)
        
    elif plottype == 'bar_timeseries':
        ax = data.plot(kind='bar', color=color, **kwargs)
        if isinstance(data, pd.Series):
            plot_values_above_bar(data, orient=orient, strfmt=strfmt)
        else:
            for i, col in enumerate(data.columns):
                plot_values_above_bar(data[col], orient=orient, strfmt=strfmt,
                                      bar_nr=i, nr_bars=len(data.columns))
    
    elif plottype == 'line_timeseries':
        ax = data.plot(color=color, **kwargs)
        
    elif plottype == 'scatter':
        x = data.iloc[:, 0]
        y = data.iloc[:, 1]
        try:
            size = data.iloc[:, 2]
        except IndexError:
            size = None
        ax = sns.scatterplot(x=x, y=y, size=size, color='grey', **kwargs)
    elif plottype == 'composition_comparison':
        ax = data.transpose().plot(kind='barh', stacked=True, color=color, **kwargs)
        data_begin = data.cumsum().shift().fillna(0)
        data_end = data.cumsum()
        location = data_begin.add(data_end).div(2)
        if not isinstance(highlight, int):
            raise TypeError('Can only highlight one line in composition comparison')
   
        plot_values_above_bar(location.iloc[highlight, :], data.iloc[highlight, :],
                              textcolor='white', orient=orient, strfmt=strfmt)
        
    elif plottype == 'piechart':
        raise TypeError('A piechart? Are you kidding me?')
    else:
        raise NotImplementedError(f'plottype {plottype} not available, choose "bar", or "waterfall"')
    plt.box(False)
    if orient == 'v' and plottype != 'scatter':
        plt.xticks([])
    elif orient == 'h' and plottype not in  ['line_timeseries', 'scatter']:
        plt.yticks([])
    return ax

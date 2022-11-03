#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 05:53:52 2020

@author: hbatistuzzo
"""

# ######
# drive api password: Q9uHI9BbwzKQSpRiuwm
# access url: https://podaac-tools.jpl.nasa.gov/drive/files
# ######
from pylab import text
import numpy as np
import netCDF4 as nc
import xarray as xr
import multiprocessing as mp
import os
import time
import humanize
import matplotlib.pyplot as plt
# from mpl_toolkits.basemap import Basemap, addcyclic, shiftgrid
import matplotlib.cbook
import cartopy
import cartopy.feature as cfeature
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from cartopy.util import add_cyclic_point
from matplotlib.axes import Axes
from cartopy.mpl.geoaxes import GeoAxes
GeoAxes._pcolormesh_patched = Axes.pcolormesh
# warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)
import cmocean
from dask.diagnostics import ProgressBar
from dask.distributed import Client
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
print("imported packages...")


def stats(vari):
    mu = np.nanmean(vari)
    sigma = np.nanstd(vari)
    vari_min = np.nanmin(vari)
    vari_max = np.nanmax(vari)
    # print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {vari_min:.2f}, max is {vari_max:.2f}')
    return mu, sigma, vari_min, vari_max
###############################################################################
# Fur der Hovmoller
ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ldir1='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/hovs/'


ds_test = xr.open_dataset(ldir1+ 'CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0_90.0.nc')
lats = ds_test.lat.values
lons = ds_test.lon.values

ds = xr.open_mfdataset(ldir1+'*.nc', combine='nested', concat_dim='lat',parallel=True)
ds2 = ds.reindex(lat=sorted(ds.lat))

sst_monthly_mean=ds2.analysed_sst.groupby('time.month').mean(dim='time',skipna=True,keep_attrs=False).load()
sst_monthly_std=ds2.analysed_sst.groupby('time.month').std(dim='time',skipna=True,keep_attrs=False).load()

# #open_mfdataset aint gonna work here. We need a loop

# datasets = []
# with ProgressBar():
#     for lat in lats:
#         ds = xr.open_dataset(ldir1+'CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0_'+str(lat)+'.nc')
#         datasets.append(ds)
#         ds.close()
# tic()
# #combine everything!
# combined = xr.concat(datasets, dim='lat')
# toc()


lat = sst_monthly_mean.lat.values
lon = sst_monthly_mean.lon.values

ddd = {'lat': {'dims': 'lat','data': lat, 'attrs': {'units': 'deg'}},
       'lon': {'dims': 'lon', 'data': lon, 'attrs': {'units': 'deg'}}}

from collections import OrderedDict as od
z_c1 = od()
z_c1['sst_mean'] = sst_monthly_mean
# z_c1['sst_std'] = sst_std.values


encoding = {}
for key in z_c1.keys():
    ddd.update({key: {'dims': ('lat','month','lon'), 'data': z_c1[key],
                          'attrs': {'units': 'Kelvin'}}})
    encoding.update({key: {'dtype': 'float32', 'scale_factor': 0.01,
                                'zlib': True}})

ds3 = xr.Dataset.from_dict(ddd)
ds3.load().to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/monthly_means.nc', format='NETCDF4',
             encoding=encoding)

sst_mean.data.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/full_mean.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True}})

#std
from collections import OrderedDict as od
z_c1 = od()
z_c1['sst_std'] = sst_monthly_std


encoding = {}
for key in z_c1.keys():
    ddd.update({key: {'dims': ('lat','month','lon'), 'data': z_c1[key],
                          'attrs': {'units': 'Kelvin'}}})
    encoding.update({key: {'dtype': 'float32', 'scale_factor': 0.01,
                                'zlib': True}})

ds3 = xr.Dataset.from_dict(ddd)
ds3.load().to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/monthly_stds.nc', format='NETCDF4',
             encoding=encoding)

sst_mean.data.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/full_mean.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True}})

#done




##############
# Retrieve and plot

#lets bring up the dask monitor. http://localhost:8787/status
# client = Client()
client = Client() #ok lets try this
client

ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ds_mean = xr.open_dataset(ldir0+'monthly_means.nc')
sst_mean = ds_mean.sst_mean.values - 273

#plotting monthly means
lon = ds_mean.lon.values
lat = ds_mean.lat.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)

sst = {}
namespace = globals()
sst_list=[]
month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for m in np.arange(0,12):
    sst[month[m]] = ds_mean.sst_mean.sel(month=m)
    sst[month[m]] = sst[month[m]].values - 273
    # sst_list.append(sst.isel(month=m).values) #this works for separating the months
    # namespace[f'sst_mean_{month[m]}'] = ds_mean[m] #separates the 12 dataarrays by name
    print('this worked')

#argh fix the scale
sst[month[m]] = sst[month[m]].values - 273

#for a fixed colorbar, lets get the mean of the means and the mean of the stds
mu = round(np.nanmean(sst_mean),4)
sigma = round(np.nanstd(sst_mean),4)
z_min = round(np.nanmin(sst_mean),4)
z_max = round(np.nanmax(sst_mean),4)
print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {z_min:.2f}, max is {z_max:.2f}')

[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])
ticks = [sm,m,ms]
gfont = {'fontname':'Helvetica','fontsize' : 16}

# ssm = ssm
# mss = mss
# ticks_sst_mean = [sm,m,ms]
ticks_up=np.arange(0,31,step=5)
# gfont = {'fontsize' : 16}

for mon in sst.keys():
    # mu = round(np.nanmean(sst[mon]),2)
    # sigma = round(np.nanstd(sst[mon]),2)
    # sst_min = round(np.nanmin(sst[mon]),2)
    # sst_max = round(np.nanmax(sst[mon]),2)
    # print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {z_min:.2f}, max is {z_max:.2f}')
    # [ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
    #          np.around(mu-sigma,decimals=2),
    #          np.around(mu,decimals=2),
    #          np.around(mu+sigma,decimals=2),
    #          np.around(mu+2*sigma,decimals=2)]
    # print([ssm,sm,m,ms,mss])
    # ticks_sst_mean = [sm,m,ms]
    lons = ds_mean.lon.values
    fig = plt.figure(figsize=(8,6),dpi=300)
    ax = plt.axes(projection=ccrs.Robinson())
    ax.coastlines(resolution='50m', color='black', linewidth=0.25)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.05,zorder=2)
    ax.add_feature(cfeature.LAND, edgecolor='black',linewidths=0.05,zorder=3)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1,zorder=4,alpha=0.5)
    ax.add_feature(cfeature.BORDERS, linewidths=0.1,zorder=5)
    ax.add_feature(cfeature.RIVERS, linewidths=0.25,zorder=6)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.set_global()
    CS = plt.contour(lon2d, lat2d, sst[mon], transform=ccrs.PlateCarree(),linewidths=0.25,colors='k',
                  levels=[sm,m,ms],zorder=1)
    fmt = {} 
    strs = ['$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$']
    for l, s in zip(CS.levels, strs): 
        fmt[l] = s
    ax.clabel(CS, CS.levels, inline=True,fontsize=5,fmt=fmt)
    cf = plt.pcolormesh(lon2d, lat2d, sst[mon],transform=ccrs.PlateCarree(), 
                        shading='auto',cmap=cmocean.cm.thermal,vmin=0,vmax=31,zorder=0)
    plt.title(f"CMC-GHRSST 'Analysed SST' 1991-2017 {mon} mean",fontdict = gfont,pad = 20)
    gl = ax.gridlines(draw_labels=True,xlocs=np.arange(-120, 121, 60),
                      ylocs=np.arange(-90, 91, 30),
                      linewidth=0.25,color='black',zorder = 7)
    # gl.xlocator = mticker.FixedLocator([-180, -90,-45, 0, 45, 90,180])
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}
    gl.rotate_labels = False
    gl.ypadding = 30
    gl.xpadding = 10
    cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks, extend='both')
    cbar.set_label('Analysed SST (\u00B0C))')
    pos = cbar.ax.get_position()
    cbar.ax.set_aspect('auto')
    ax2 = cbar.ax.twiny()
    cbar.ax.set_position(pos)
    ax2.set_position(pos)
    cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",ticks=ticks_up,extend='both')
    cbar2.ax.xaxis.set_ticks_position('top')
    cbar.ax.set_xticklabels([f'$\mu$-$\sigma$ = {sm:.2f}', f'$\mu$ = {m:.2f}',
                              f'$\mu$+$\sigma$ = {ms:.2f}'])
    cbar.ax.get_yaxis().set_ticks([])
    text(0, 0, f'MIN = {z_min:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
    text(1, 0, f'MAX = {z_max:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
    # if not (os.path.exists(ldir0 + 'full_sst_std.png')):
    #     plt.savefig(ldir0 + 'full_sst_std.png',bbox_inches='tight')
    if not (os.path.exists(ldir0 + f'sst_{mon}_mean_global2.png')):
        plt.savefig(ldir0 + f'sst_{mon}_mean_global2.png',bbox_inches='tight')
    plt.show()





############################
#now for the Ilhas region


ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ds = xr.open_dataset(ldir0+'monthly_means.nc')


#archipelago:00°55′1″N 29°20′45″W or 0.91694444 N, 29.34583333 W
lat_SPSP_S = 0.8
    #lon_SPSP_S -55 to 15
lat_SPSP_N = 1.2

lat_5N = 5
    #lon_5N -55 to -5
lat_5S = -5
    #lon_5N -40 to 15

# adt_hov = adt.sel(latitude=5.125, longitude=slice(305,355))
sst_ilhas = ds.sst_mean.sel(lat=slice(-10,10),lon=slice(-60,15))
z = sst_ilhas.values -273

#plotting monthly means
lon = sst_ilhas.lon.values
lat = sst_ilhas.lat.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)



sst = {}
namespace = globals()
sst_list=[]
month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for m in np.arange(0,12):
    sst[month[m]] = sst_ilhas.sel(month=m)
    sst[month[m]] = sst[month[m]].values - 273
    # sst_list.append(sst.isel(month=m).values) #this works for separating the months
    # namespace[f'sst_mean_{month[m]}'] = ds_mean[m] #separates the 12 dataarrays by name
    print('this worked')

#argh fix the scale
# sst[month[m]] = sst[month[m]].values - 273


ssm = ssm
mss = mss
ticks_sst_mean = [sm,m,ms]
ticks_up=np.arange(0,31,step=5)
gfont = {'fontsize' : 16}

for mon in sst.keys():
    mu = round(np.nanmean(sst[mon]),2)
    sigma = round(np.nanstd(sst[mon]),2)
    sst_min = round(np.nanmin(sst[mon]),2)
    sst_max = round(np.nanmax(sst[mon]),2)
    print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {sst_min:.2f}, max is {sst_max:.2f}')
    [ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
    print([ssm,sm,m,ms,mss])
    ticks_sst_mean = [sm,m,ms]
    # lons = ds_mean.lon.values
    fig = plt.figure(figsize=(7, 5),dpi= 300)
    ax1 = plt.axes(projection=ccrs.PlateCarree())
    # ax1 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree(central_longitude=0))
    ax1.set_extent([-60.01, 15.01, -10.05, 10.05], ccrs.PlateCarree(central_longitude=0))
    # ax1.set_yticks([-10, -5, 0, 5, 10]); ax1.set_yticklabels(y_tick_labels)
    # ax1.set_xticks([-60, -45, -30, -15, 0, 15]); ax1.set_xticklabels(x_tick_labels)
    ax1.coastlines(resolution='50m', color='black', linewidth=0.25)
    ax1.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.05,zorder=2)
    ax1.add_feature(cfeature.LAND, edgecolor='black',linewidths=0.05,zorder=3)
    ax1.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1,zorder=4,alpha=0.5)
    ax1.add_feature(cfeature.BORDERS, linewidths=0.1,zorder=5)
    ax1.add_feature(cfeature.RIVERS, linewidths=0.25,zorder=6)
    ax1.add_feature(cartopy.feature.OCEAN)
    cf = plt.pcolormesh(lon2d, lat2d, sst[mon],transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.thermal)
    plt.title(f"CMC-GHRSST 'Analysed SST' 1991-2017 {mon} mean",fontdict = gfont,pad = 20)
    gl = ax1.gridlines(draw_labels=True,xlocs=np.arange(-60, 16, 15),
                      ylocs=np.arange(-10, 11, 5),
                      linewidth=0.25,color='black',zorder = 7,alpha=0.7,linestyle='-')
    gl.xlabels_top = False
    gl.ylabels_right = False
    # ax1.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    gl.ypadding = 10
    gl.xpadding = 10
    # Add archipelago
    # patches = [Circle((-29.34583333, 0.91694444), radius=0.35, color='black')]
    # for p in patches:
    #     ax1.add_patch(p)
    cbar = plt.colorbar(ax=ax1,orientation="horizontal",ticks=ticks_sst_mean,extend='both')
    cbar.set_label('Analysed SST (\u00B0C)',fontsize=12)
    pos = cbar.ax.get_position()
    cbar.ax.set_aspect('auto')
    ax2 = cbar.ax.twiny()
    cbar.ax.set_position(pos)
    ax2.set_position(pos)
    cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",extend='both')
    cbar2.ax.xaxis.set_ticks_position('top')
    cbar.ax.set_xticklabels([f'$\mu$-$\sigma$ = {sm:.1f}', f'$\mu$ = {m:.1f}',
                              f'$\mu$+$\sigma$ = {ms:.1f}'],fontsize=7)
    # cbar.ax.text(22.2,27,f'MIN\n{sst_min:.2f}',ha='center',va='center')
    # cbar.ax.text(31.8,27,f'MAX\n{sst_max:.2f}',ha='center',va='center')
    CS = ax1.contour(lon, lat, sst[mon], transform=ccrs.PlateCarree(),levels=[ssm,sm,m,ms,mss],
                     linewidths=0.35,colors='k',zorder=1,inline=True)
    fmt = {} 
    strs = ['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+2$\sigma$']
    for l, s in zip(CS.levels, strs): 
        fmt[l] = s
    ax1.clabel(CS, CS.levels, inline=True,fontsize=6,fmt=fmt)
    # if not (os.path.exists(ldir0 + f'ilhas_full_sst_{mon}_mean3.png')):
    #     plt.savefig(ldir0 + f'ilhas_full_sst_{mon}_mean3.png',bbox_inches='tight')


#and the std

ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ds = xr.open_dataset(ldir0+'monthly_stds.nc')


#archipelago:00°55′1″N 29°20′45″W or 0.91694444 N, 29.34583333 W
lat_SPSP_S = 0.8
    #lon_SPSP_S -55 to 15
lat_SPSP_N = 1.2

lat_5N = 5
    #lon_5N -55 to -5
lat_5S = -5
    #lon_5N -40 to 15

# adt_hov = adt.sel(latitude=5.125, longitude=slice(305,355))
sst_ilhas = ds.sst_std.sel(lat=slice(-10,10),lon=slice(-60,15))
z = sst_ilhas.values

#plotting monthly means
lon = sst_ilhas.lon.values
lat = sst_ilhas.lat.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)



sst = {}
namespace = globals()
sst_list=[]
month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for m in np.arange(0,12):
    sst[month[m]] = sst_ilhas.sel(month=m)
    sst[month[m]] = sst[month[m]].values
    # sst_list.append(sst.isel(month=m).values) #this works for separating the months
    # namespace[f'sst_mean_{month[m]}'] = ds_mean[m] #separates the 12 dataarrays by name
    print('this worked')

#argh fix the scale
# sst[month[m]] = sst[month[m]].values - 273


ssm = ssm
mss = mss
ticks_sst_mean = [sm,m,ms]
ticks_up=np.arange(0,31,step=5)
gfont = {'fontsize' : 16}

for mon in sst.keys():
    mu = round(np.nanmean(sst[mon]),2)
    sigma = round(np.nanstd(sst[mon]),2)
    sst_min = round(np.nanmin(sst[mon]),2)
    sst_max = round(np.nanmax(sst[mon]),2)
    print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {sst_min:.2f}, max is {sst_max:.2f}')
    [ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
    print([ssm,sm,m,ms,mss])
    ticks_sst_mean = [sm,m,ms]
    lons = ds_mean.lon.values
    fig = plt.figure(figsize=(7, 5),dpi= 300)
    ax1 = plt.axes(projection=ccrs.PlateCarree())
    # ax1 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree(central_longitude=0))
    ax1.set_extent([-60.01, 15.01, -10.05, 10.05], ccrs.PlateCarree(central_longitude=0))
    # ax1.set_yticks([-10, -5, 0, 5, 10]); ax1.set_yticklabels(y_tick_labels)
    # ax1.set_xticks([-60, -45, -30, -15, 0, 15]); ax1.set_xticklabels(x_tick_labels)
    ax1.coastlines(resolution='50m', color='black', linewidth=0.25)
    ax1.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.05,zorder=2)
    ax1.add_feature(cfeature.LAND, edgecolor='black',linewidths=0.05,zorder=3)
    ax1.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1,zorder=4,alpha=0.5)
    ax1.add_feature(cfeature.BORDERS, linewidths=0.1,zorder=5)
    ax1.add_feature(cfeature.RIVERS, linewidths=0.25,zorder=6)
    ax1.add_feature(cartopy.feature.OCEAN)
    cf = plt.pcolormesh(lon2d, lat2d, sst[mon],transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.amp,
                        vmin=0,vmax=1.5)
    plt.title(f"CMC-GHRSST 'Analysed SST' 1991-2017 {mon} mean",fontdict = gfont,pad = 20)
    gl = ax1.gridlines(draw_labels=True,xlocs=np.arange(-60, 16, 15),
                      ylocs=np.arange(-10, 11, 5),
                      linewidth=0.25,color='black',zorder = 7,alpha=0.7,linestyle='-')
    gl.xlabels_top = False
    gl.ylabels_right = False
    # ax1.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    gl.ypadding = 10
    gl.xpadding = 10
    # Add archipelago
    patches = [Circle((-29.34583333, 0.91694444), radius=0.35, color='black')]
    for p in patches:
        ax1.add_patch(p)
    cbar = plt.colorbar(ax=ax1,orientation="horizontal",ticks=ticks_sst_mean,extend='max')
    cbar.set_label('Analysed SST (\u00B0C)',fontsize=12)
    pos = cbar.ax.get_position()
    cbar.ax.set_aspect('auto')
    ax2 = cbar.ax.twiny()
    cbar.ax.set_position(pos)
    ax2.set_position(pos)
    cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",extend='max')
    cbar2.ax.xaxis.set_ticks_position('top')
    # cbar.ax.set_xticklabels([f'$\mu$ = {m:.2f}',
    #                       f'$\mu$+$\sigma$ = {ms:.2f}',f'$\mu$+2$\sigma$ = {mss:.2f}'],fontsize=6)
    cbar.ax.set_xticklabels([f'$\mu$',
                      f'$\mu$+$\sigma$',f'$\mu$+2$\sigma$'])
    # cbar.ax.text(22.2,27,f'MIN\n{sst_min:.2f}',ha='center',va='center')
    # cbar.ax.text(31.8,27,f'MAX\n{sst_max:.2f}',ha='center',va='center')
    CS = ax1.contour(lon, lat, sst[mon], transform=ccrs.PlateCarree(),levels=[ssm,sm,m,ms,mss],
                     linewidths=0.35,colors='k',zorder=1,inline=True)
    fmt = {} 
    strs = ['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+2$\sigma$']
    for l, s in zip(CS.levels, strs): 
        fmt[l] = s
    ax1.clabel(CS, CS.levels, inline=True,fontsize=7,fmt=fmt)
    if not (os.path.exists(ldir0 + f'ilhas_full_sst_{mon}_std.png')):
        plt.savefig(ldir0 + f'ilhas_full_sst_{mon}_std.png',bbox_inches='tight')



##### make a video
import cv2
import argparse
import os
from pathlib import Path
paths = sorted(Path('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/monthly/mean_again/').iterdir(), key=os.path.getmtime)

# Construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-ext", "--extension", required=False, default='png', help="extension name. default is 'png'.")
ap.add_argument("-o", "--output", required=False, default='output.mp4', help="output video file")
args = vars(ap.parse_args())

# Arguments
dir_path = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/monthly/mean_again/'
ext = args['extension']
output = args['output']

images = []
for f in sorted(os.listdir(dir_path),key=os.path.getmtime):
    if f.endswith(ext):
        images.append(f)

# Determine the width and height from the first image
image_path = os.path.join(dir_path, images[0])
frame = cv2.imread(image_path)
cv2.imshow('video',frame)
height, width, channels = frame.shape

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be sure to use lower case
out = cv2.VideoWriter(output, fourcc, 2.0, (width, height))

for image in images:

    image_path = os.path.join(dir_path, image)
    frame = cv2.imread(image_path)

    out.write(frame) # Write out frame to video

    cv2.imshow('video',frame)
    if (cv2.waitKey(1) & 0xFF) == ord('q'): # Hit `q` to exit
        break

# Release everything if job is finished
out.release()
cv2.destroyAllWindows()

print("The output video is {}".format(output))

####################################### and for the std


ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ds = xr.open_dataset(ldir0+'monthly_stds.nc')


#archipelago:00°55′1″N 29°20′45″W or 0.91694444 N, 29.34583333 W
lat_SPSP_S = 0.8
    #lon_SPSP_S -55 to 15
lat_SPSP_N = 1.2

lat_5N = 5
    #lon_5N -55 to -5
lat_5S = -5
    #lon_5N -40 to 15

z = ds.sst_std

#plotting monthly means
lon = ds.sst_std.lon.values
lat = ds.sst_std.lat.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)



sst = {}
namespace = globals()
sst_list=[]
month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for m in np.arange(0,12):
    sst[month[m]] = z.sel(month=m)
    sst[month[m]] = sst[month[m]].values
    # sst_list.append(sst.isel(month=m).values) #this works for separating the months
    # namespace[f'sst_mean_{month[m]}'] = ds_mean[m] #separates the 12 dataarrays by name
    print('this worked')

#argh fix the scale
# sst[month[m]] = sst[month[m]].values - 273


#for a fixed colorbar, lets get the mean of the means and the mean of the stds
mu = round(np.nanmean(z),4)
sigma = round(np.nanstd(z),4)
z_min = round(np.nanmin(z),4)
z_max = round(np.nanmax(z),4)
print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {z_min:.2f}, max is {z_max:.2f}')

[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])
# ticks_inss = [ssm,sm,m,ms,mss]
ticks = [0,sm,m,ms,mss]
gfont = {'fontsize' : 16}

for mon in sst.keys():
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax = plt.axes(projection=ccrs.Mollweide())
    z = sst[mon]
    # z, lons = shiftgrid(180., z, lons, start=False)
    ax = plt.axes(projection=ccrs.Robinson())
    # CS = plt.contour(lon2d, lat2d, z, transform=ccrs.PlateCarree(),linewidths=0.25,colors='k',
    #               levels=[sm,m,ms],zorder=1)
    # fmt = {} 
    # strs = ['$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$']
    # for l, s in zip(CS.levels, strs): 
    #     fmt[l] = s
    # ax.clabel(CS, CS.levels, inline=True,fontsize=5,fmt=fmt)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.1,zorder=2)
    ax.add_feature(cfeature.LAND, zorder=3,edgecolor='black',linewidths=0.25)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1,zorder=4)
    ax.add_feature(cfeature.BORDERS, linewidths=0.25,zorder=5)
    ax.add_feature(cfeature.RIVERS, linewidths=0.25,zorder=6)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.set_global()

    plt.title(f"CMC-GHRSST 'Analysed SST' {mon} 1991-2017 STD",fontdict = gfont,pad = 20)
    cf = plt.pcolormesh(lon2d, lat2d, z,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.amp,
                    vmin=0,vmax=mss,zorder=0)
    cbar = plt.colorbar(ax=ax,orientation="horizontal",extend='max',ticks=ticks,pad=0.1)
    cbar.set_label('Analysed SST (\u00B0C))')
    pos = cbar.ax.get_position()
    cbar.ax.set_aspect('auto')
    ax2 = cbar.ax.twiny()
    cbar.ax.set_position(pos)
    ax2.set_position(pos)
    cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",ticks=ticks,extend='max')
    cbar2.ax.xaxis.set_ticks_position('top')
    cbar2.ax.set_xticklabels(['0','$\mu$-$\sigma$','$\mu$','$\mu$+$\sigma$','2$\mu$+$\sigma$']) 
    # gl.xlabel_style = {'size': 15, 'color': 'gray'}
    # gl.xlabel_style = {'color': 'red', 'weight': 'bold'}
    # gl.ylocator = mticker.FixedLocator([-40,-30,-20,-10,0])
    # lon_formatter = LongitudeFormatter(zero_direction_label=True)
    gl = ax.gridlines(draw_labels=True,xlocs=np.arange(-120, 121, 60),
                  ylocs=np.arange(-90, 91, 30),
                  linewidth=0.25,color='black',zorder = 7)
    # gl.xlocator = mticker.FixedLocator([-180, -90,-45, 0, 45, 90,180])
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}
    gl.rotate_labels = False
    gl.ypadding = 30
    gl.xpadding = 10
    cbar.ax.get_yaxis().set_ticks([])
    # cbar.ax.text(ssm-2,0.3,f'MIN\n{z_min:.2f}',ha='center',va='center')
    # cbar.ax.text(mss+2,0.3,f'MAX\n{z_max:.2f}',ha='center',va='center')
    # ax.set_aspect('auto')
    ax.set_aspect('auto')
    text(0, 0, f'MIN = {z_min:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
    text(1, 0, f'MAX = {z_max:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
    if not (os.path.exists(ldir0 + f'sst_{mon}_std_global.png')):
        plt.savefig(ldir0 + f'sst_{mon}_std_global.png',bbox_inches='tight')
    plt.show()
plt.show()


#film..
import cv2
import argparse
import os
from pathlib import Path
paths = sorted(Path('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/monthly/std/new/').iterdir(), key=os.path.getmtime)

# Construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-ext", "--extension", required=False, default='png', help="extension name. default is 'png'.")
ap.add_argument("-o", "--output", required=False, default='output.mp4', help="output video file")
args = vars(ap.parse_args())

# Arguments
dir_path = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/monthly/std/new/'
ext = args['extension']
output = args['output']

images = []
for f in sorted(os.listdir(dir_path),key=os.path.getmtime):
    if f.endswith(ext):
        images.append(f)

# Determine the width and height from the first image
image_path = os.path.join(dir_path, images[0])
frame = cv2.imread(image_path)
cv2.imshow('video',frame)
height, width, channels = frame.shape

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be sure to use lower case
out = cv2.VideoWriter(output, fourcc, 2.0, (width, height))

for image in images:

    image_path = os.path.join(dir_path, image)
    frame = cv2.imread(image_path)

    out.write(frame) # Write out frame to video

    cv2.imshow('video',frame)
    if (cv2.waitKey(1) & 0xFF) == ord('q'): # Hit `q` to exit
        break

# Release everything if job is finished
out.release()
cv2.destroyAllWindows()

print("The output video is {}".format(output))





#### 23/01 something very weird happened. lets redo the plots
ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ds = xr.open_dataset(ldir0+'full_mean.nc')

datar = ds.sst_mean.values -273

lon = ds.lon.values
lat = ds.lat.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)

mu = np.nanmean(datar)
sigma = np.nanstd(datar)
sst_min = np.nanmin(datar)
sst_max =np.nanmax(datar)
print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {sst_min:.2f}, max is {sst_max:.2f}')



[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])
# ticks_inss = [ssm,sm,m,ms,mss]
ticks = [sm,m,ms]


fig = plt.figure(figsize=(8,6),dpi=300)
ax = plt.axes(projection=ccrs.Robinson())
ax.coastlines(resolution='50m', color='black', linewidth=0.25)
ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.05,zorder=2)
ax.add_feature(cfeature.LAND, edgecolor='black',linewidths=0.05,zorder=3)
ax.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1,zorder=4,alpha=0.5)
ax.add_feature(cfeature.BORDERS, linewidths=0.1,zorder=5)
ax.add_feature(cfeature.RIVERS, linewidths=0.25,zorder=6)
ax.add_feature(cartopy.feature.OCEAN)
ax.set_global()
CS = plt.contour(lon2d, lat2d, datar, transform=ccrs.PlateCarree(),linewidths=0.25,colors='k',
                  levels=[sm,m,ms],zorder=1)
fmt = {} 
strs = ['$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$']
for l, s in zip(CS.levels, strs): 
    fmt[l] = s
ax.clabel(CS, CS.levels, inline=True,fontsize=5,fmt=fmt)
cf = plt.pcolormesh(lon2d, lat2d, datar,transform=ccrs.PlateCarree(), shading='auto',
                    cmap=cmocean.cm.thermal,zorder=0)
plt.title("CMC-GHRSST 'Analysed SST' 1991-2017 mean",pad = 20)
gl = ax.gridlines(draw_labels=True,xlocs=np.arange(-120, 121, 60),
                  ylocs=np.arange(-90, 91, 30),
                  linewidth=0.25,color='black',zorder = 7)
# gl.xlocator = mticker.FixedLocator([-180, -90,-45, 0, 45, 90,180])
gl.xlabel_style = {'size': 10, 'color': 'black'}
gl.ylabel_style = {'size': 10, 'color': 'black'}
gl.rotate_labels = False
gl.ypadding = 30
gl.xpadding = 10
cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks,extend='both')
cbar.set_label('Analysed SST (\u00B0C))')
pos = cbar.ax.get_position()
cbar.ax.set_aspect('auto')
ax2 = cbar.ax.twiny()
cbar.ax.set_position(pos)
ax2.set_position(pos)
cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",extend='both')
cbar2.ax.xaxis.set_ticks_position('top')
cbar.ax.set_xticklabels(['$\mu$-$\sigma$ = 3.31', '$\mu$ = 14.46',
                          '$\mu$+$\sigma$ = 25.62'])
cbar.ax.get_yaxis().set_ticks([])
text(0, 0, f'MIN = {sst_min:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
text(1, 0, f'MAX = {sst_max:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
# if not (os.path.exists(ldir0 + 'full_sst_mean.png')):
#     plt.savefig(ldir0 + 'full_sst_mean.png',bbox_inches='tight')
plt.show()


#################################### 25/01 Ilhas
# 1) CMEMS FULL SERIES PLOTS
ldir0 = r"/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/"
path = 'monthly_means.nc'
ds = xr.open_dataset(ldir0+path) # Means and STDs for ADT, SLA, UGOS, VGOS, UGOSA, VGOSA

#Define the region
latN = 10
latS = -10
lonW = 65.5
lonE = 15.5

vari = ds.sst_mean
lon = vari.lon.values # 1440 array float32
lat = vari.lat.values # 720 ~~~

vari = ds.sst_mean.sel(lat=slice(-10,10),lon=slice(-60,15))
variv = vari.values -273 #new vari!!!!

#### the new lon needs to be this size!
lon = vari.lon.values 
lat = vari.lat.values 

lon2d, lat2d = np.meshgrid(lon, lat)

# 2) Get some stats:
mu, sigma, vari_min, vari_max = stats(variv)

# 3) Set colorbar intervals
[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])

# 4) aux
ticks_var = [ssm,sm,m,ms,mss]
gfont = {'fontsize' : 20}
# 'Absolute Dynamic Topography (m)','Zonal Geostrophic Velocity (m/s)', 'Meridional Geostrophic Velocity (m/s)'

var = {}
namespace = globals()
var_list=[]
for m in np.arange(0,12):
    var[month[m]] = vari[:,m,:].values
    var_list.append(vari[:,m,:].values) #this works for separating the months
    namespace[f'sst_mean_{month[m]}'] = vari[m] #separates the 12 dataarrays by name
    print('this worked')


ssm = ssm
mss = mss
ticks_sst_mean = [ssm,sm,m,ms,mss]
ticks_up=np.arange(20,31,step=1)
gfont = {'fontsize' : 16}


#lon2d (101,376)


figs = []
for mon in var.keys():
    variv = var[mon] -273
    mu, sigma, vari_min, vari_max = stats(variv)
    [ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
    print([ssm,sm,m,ms,mss])
    ticks_var = [ssm,sm,m,ms,mss]
    fig = plt.figure(figsize=(8,6),dpi=300)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-60.01, 15.01, -10.05, 10.05], ccrs.PlateCarree(central_longitude=0))
    arch = ax.plot(-29.34583333,0.91694444, 'k*', markersize=3, markeredgewidth = 0.25, transform=ccrs.PlateCarree()) # WHY
    CS = plt.contour(lon2d, lat2d, variv, transform=ccrs.PlateCarree(),linewidths=0.5,colors='k',
              levels=[ssm,sm,m,ms,mss],zorder=1)
    fmt = {} 
    strs = ['$\mu$-$2\sigma$','$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+$2\sigma$']
    for l, s in zip(CS.levels, strs): 
        fmt[l] = s
    ax.clabel(CS, CS.levels, inline=True,fontsize=7,fmt=fmt)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.1)
    ax.add_feature(cfeature.LAND, zorder=1,edgecolor='black',linewidths=0.25)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1)
    ax.add_feature(cfeature.BORDERS, linewidths=0.25)
    ax.add_feature(cfeature.RIVERS, linewidths=0.5)
    ax.set_extent([-65, 15, -10.1, 10.1], crs=ccrs.PlateCarree())
    states_provinces = cfeature.NaturalEarthFeature(category='cultural',
                                                    name='admin_1_states_provinces_lines',
    scale='50m',facecolor='none')
    ax.add_feature(states_provinces, edgecolor='gray',linewidths=0.25)

    plt.title(f"CMC-GHRSST 'Analysed SST' 1991-2017 {mon} mean",fontdict = gfont)
    cf = plt.pcolormesh(lon2d, lat2d, variv,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.thermal,
                        vmin=20,vmax=31,zorder=0)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                 linewidth=0.25, color='black', alpha=0.5, linestyle='dashed')
    gl.xlabels_top = False
    gl.ylabels_right = False
    # gl.xlines = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.ylocator = mticker.FixedLocator([-10,-5,0,5,10])
    cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks_var,pad=0.12)
    cbar.set_label('Analysed SST (\u00B0C)',fontsize=12)
    pos = cbar.ax.get_position()
    cbar.ax.set_aspect('auto')
    ax2 = cbar.ax.twiny()
    cbar.ax.set_position(pos)
    ax2.set_position(pos)
    cbar2 = plt.colorbar(cax=ax2, orientation="horizontal")
    cbar2.ax.xaxis.set_ticks_position('top')
    cbar.ax.set_xticklabels(['$\mu$-2$\sigma$','$\mu$-$\sigma$', '$\mu$',
                              '$\mu$+$\sigma$','$\mu$+2$\sigma$'],fontsize=7)
    text(0, -0.8, f'MIN = {vari_min:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
    text(1, -0.8, f'MAX = {vari_max:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
    if not (os.path.exists(ldir0 + f'sst_{mon}_mean_ilhas.png')):
        plt.savefig(ldir0 + f'sst_{mon}_mean_ilhas.png',bbox_inches='tight')
    figs.append([fig])
    plt.show()


##### movie time
import cv2
import argparse
import os
from pathlib import Path
paths = sorted(Path('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/ilhas_region/new').iterdir(), key=os.path.getmtime)

# Construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-ext", "--extension", required=False, default='png', help="extension name. default is 'png'.")
ap.add_argument("-o", "--output", required=False, default='output.mp4', help="output video file")
args = vars(ap.parse_args())

# Arguments
dir_path = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/ilhas_region/new'
ext = args['extension']
output = args['output']

images = []
for f in sorted(os.listdir(dir_path),key=os.path.getmtime):
    if f.endswith(ext):
        images.append(f)

# Determine the width and height from the first image
image_path = os.path.join(dir_path, images[0])
frame = cv2.imread(image_path)
cv2.imshow('video',frame)
height, width, channels = frame.shape

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be sure to use lower case
out = cv2.VideoWriter(output, fourcc, 2.0, (width, height))

for image in images:

    image_path = os.path.join(dir_path, image)
    frame = cv2.imread(image_path)

    out.write(frame) # Write out frame to video

    cv2.imshow('video',frame)
    if (cv2.waitKey(1) & 0xFF) == ord('q'): # Hit `q` to exit
        break

# Release everything if job is finished
out.release()
cv2.destroyAllWindows()

print("The output video is {}".format(output))




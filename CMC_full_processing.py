#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 22:29:51 2020

@author: hbatistuzzo
"""
# ######
# drive api password: Q9uHI9BbwzKQSpRiuwm
# access url: https://podaac-tools.jpl.nasa.gov/drive/files
# ######
import numpy as np
import netCDF4 as nc
import xarray as xr
import multiprocessing as mp
import os
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
from pylab import text
import datetime as dt
print("imported packages...")


def stats(vari):
    mu = np.nanmean(vari)
    sigma = np.nanstd(vari)
    vari_min = np.nanmin(vari)
    vari_max = np.nanmax(vari)
    print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {vari_min:.2f}, max is {vari_max:.2f}')
    return mu, sigma, vari_min, vari_max

def get_aux():
    # red auxiliary data (lat,lon,time) from one of the netcdf files
    # x from 0.125 to 359.875 y from -89.875 to 89.875
    # fn = '/data0/cmems/big_hovmollers/' +\
    #      'xr_global_allsat_phy_l4_000.125_1993_2019.nc'
    fn = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/hovs/CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0_1.0.nc'
    ds = xr.open_dataset(fn)
    x = ds['lon'][:].data
    nx = x.shape[0]
    y = ds['lon'][:].data
    ny = y.shape[0]
    t = ds['time'][:].data
    nt = t.shape[0]
    tt = np.arange(0,nt,1)
    # cmems series starts at 1/1/1993
    # if np.diff(ds['time'][:]).max() != 1:
    #     raise Exception('There should be no gaps in the time series. \
    #     You probably missed a CMEMS map file.')
    time = [dt.date(1993, 1, 1) + dt.timedelta(days=xx) for xx in range(0, len(tt))]
    jtime = [dt.date.toordinal(time[j]) for j in range(nt)]
    jtime = np.asarray(jtime).astype('int32')
    return nx, ny, nt, x, y, time, jtime

# import numpy as np
# import matplotlib.pylab as plt
# import os
# import psutil
# import gc
# process = psutil.Process(os.getpid())
# def str_mem_usage():
#     mu = process.memory_info().rss / 1024**2
#     return 'Memory usage: {:.2f} MB'.format(mu)

# arrs = []
# for ii in range(10):
#     print('it', ii, '\t', str_mem_usage())
#     n = 10000
#     arr = np.random.rand(n**2).reshape(n, n)
#     #arrs += [arr]  # activate for memory leak, obviously

#     plt.ioff()
#     fig, ax = plt.subplots(1, 1)
#     ax.imshow(arr)
#     #plt.savefig('tmp.pdf')  # irrelevant for memory leak
#     plt.close(fig)
#     plt.ion()

#     gc.collect()  # deactivate for memory leak

#some handy functions for analytics
def TicTocGenerator():
    # Generator that returns time differences
    ti = 0           # initial time
    tf = time.time() # final time
    while True:
        ti = tf
        tf = time.time()
        yield tf-ti # returns the time difference
TicToc = TicTocGenerator() # create an instance of the TicTocGen generator
# This will be the main function through which we define both tic() and toc()
def toc(tempBool=True):
    # Prints the time difference yielded by generator instance TicToc
    tempTimeInterval = next(TicToc)
    if tempBool:
        print( "Elapsed time: %f seconds.\n" %tempTimeInterval )
def tic():
    # Records a time in TicToc, marks the beginning of a time interval
    toc(False)

def listdirs(folder):
    return [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

ldir0 = r"/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/all_backup/"

# We have 9329 daily files (25 years)
# Each is 901 x 1800 x 1 (lat, lon, time)
# Resolution is daily, 0.2 degrees
#ds = xr.open_dataset(ldir0+'19910901120000-CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0.nc')

#lets bring up the dask monitor. http://localhost:8787/status
# client = Client()
client = Client() #ok lets try this
client

fl = ldir0 + '*.nc'
fn = sorted(listdirs(ldir0))

# datasets = []
# os.chdir(ldir0)
# fn = os.listdir(ldir0)

import glob
import shutil
# import os
# for year in years:
#     for data in glob.glob(ldir0):
#         print(f'file is {data}')

# a='myfile_030811.xls'
# b = a.split('_')[1].split('.')[0]

years=np.arange(1991,2018)

for year in years:
    ldir1 = ldir0 + str(year) +'/'
    fn = sorted(os.listdir(ldir1))
    for x in fn:
        if x == str(year) +'_sst_masked.nc':
            shutil.move(ldir1 + x, '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/grouped/')



##############################################################################################
#OK now I have 27 nc files with masked data. Lets try working with them.
ldir0 = r"/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/grouped/"
fl = ldir0 + '*.nc'
fn = sorted(os.listdir(ldir0))

ds = xr.open_dataset(ldir0+fn[0])
#sst = ds.analysed_sst.data #turns into array of float32


sst2 = da.from_array(sst.values)


ds = xr.open_mfdataset(fl,combine='nested', concat_dim="time",parallel=True)

sst = ds.analysed_sst


ds=ds.chunk(1000,300,600)
ds.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/grouped/all.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True,'complevel':5}})



sst_mean = ds.analysed_sst.mean(dim='time',skipna=True,keep_attrs=False).load()

import os
import dask.array as da
from netCDF4 import Dataset
from IPython.display import Image


#lets bring up the dask monitor. http://localhost:8787/status
# client = Client()
client = Client() #ok lets try this
client

ldir0 = r"/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/grouped/"
fl = ldir0 + '*.nc'
fn = sorted(os.listdir(ldir0))

test = xr.open_dataset(ldir0+fn[0])
lats = test.lat.values

ds = xr.open_mfdataset(fl,combine='nested', concat_dim="time",parallel=True,
                       drop_variables=['analysis_error','sea_ice_fraction'])

#hovmoller maker
for lat in lats:
    a=ds.analysed_sst.sel(lat=lat)
    a.to_netcdf(f'/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/hovs/CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0_'+str(lat)+'.nc',
                format='NETCDF4', encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True,}})
    del a




ds = xr.open_dataset(ldir0+'1991_sst_masked.nc')
sst_mean = ds.analysed_sst.mean(dim='time',skipna=True,keep_attrs=False)
sst_mean.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/grouped/means/1991_mean.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True,'complevel':5}})

years=np.arange(1991,2018)
for year in years:
    ds = xr.open_dataset(ldir0+str(year)+'_sst_masked.nc')
    sst_mean = ds.analysed_sst.mean(dim='time',skipna=True,keep_attrs=False)
    sst_mean.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/grouped/means/'+str(year)+'_mean.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True,'complevel':5}})
    del sst_mean


##############################################################################################

ldir1 = ldir0 + '1994/'
fl = ldir1 + '*.nc'
ds = xr.open_mfdataset(fl,combine='nested', concat_dim="time",parallel=True,
                       drop_variables=['analysis_error','sea_ice_fraction'])
sst_masked = ds.sel()['analysed_sst'].where(ds.mask == 1).load()
sst_masked.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/all_backup/1994/1994_sst_masked.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True,'complevel':5}})

del ds, sst_masked

#test check
ds2 = xr.open_dataset(ldir0 + '1992/sst_masked.nc')


encoding={'a1':{'zlib': True,'complevel': 5}}



for year in years:
    ldir1 = ldir0 + str(year) + '/'
    fl = ldir1 + '*.nc'
    ds = xr.open_mfdataset(fl,combine='nested', concat_dim="time",parallel=True,
                       drop_variables=['analysis_error','sea_ice_fraction'])
    sst_masked = ds.sel()['analysed_sst'].where(ds.mask == 1).load()
    sst_masked.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/all_backup/'+str(year)+'/'+ str(year) +'_sst_masked.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True,'complevel':5}})
    del ds, sst_masked

for f in fn: #iterate all files
    ds = xr.open_dataset(f)
    test = ds.sel()['analysed_sst'].where(ds.mask == 1)
    datasets.append(test)
    ds.close()
    print(f'moving on to file {f}')

print('this was a huge success!')

ds_test=xr.open_dataset(ldir0+'19920412120000-CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0.nc')


#we need to filter flag_masks=1
test = ds_test.sel()['analysed_sst'].where(ds_test.mask == 1).plot()

tic()
ds = xr.open_mfdataset(fl,combine='nested', concat_dim="time",parallel=True,
                       drop_variables=['analysis_error','sea_ice_fraction','mask'])
toc()

ds_size = humanize.naturalsize(ds.nbytes)
sst = ds.analysed_sst
sst_size = humanize.naturalsize(sst.nbytes)

#get the mean of adt

sst2 = sst.chunk({'time':100})


sst_mean = sst2.mean(dim='time').load()

lat = sst2.lat.values
lon = sst2.lon.values
ddd = {'lat': {'dims': 'lat','data': lat, 'attrs': {'units': 'deg N'}},
       'lon': {'dims': 'lon', 'data': lon, 'attrs': {'units': 'deg E'}}}

from collections import OrderedDict as od
z_c1 = od()
z_c1['sst'] = sst2.values


#I think scale factor has to have 4 decimals
encoding = {}
for key in z_c1.keys():
    ddd.update({key: {'dims': ('lat', 'lon'), 'data': z_c1[key],
                          'attrs': {'units': 'K'}}})
    encoding.update({key: {'dtype': 'int16', 'scale_factor': 0.0001,
                                'zlib': True, '_FillValue': -9999999}})

ds = xr.Dataset.from_dict(ddd)
ds.to_netcdf('/media/hbatistuzzo/DATA/Era5/full_means_stds.nc', format='NETCDF4',
             encoding=encoding)

tic()
ds.to_netcdf('/home/hbatistuzzo/full_series_new.nc', format='NETCDF4',
             encoding={'analysed_sst':{'dtype': 'int16', 'scale_factor': 0.0001,
                                'zlib': True, '_FillValue': -9999999}})
toc()

with ProgressBar():
    ds.to_netcdf('home/hbatistuzzo/full_series_new.nc', format=None)

#saving the list of 9313 with only SST as a pickle
infile = open(ldir0 + 'sst_nc.pckl', 'wb')
pickle.dump(ds, infile)
infile.close()

#load the pickle
infile = open(ldir0+'sst_nc.pckl', 'rb')
sst = pickle.load(infile)
infile.close()

import os
import dask.array as da
from netCDF4 import Dataset
from IPython.display import Image

daskarray = da.from_array(sst.variables['analysed_sst'], chunks=(1,901,1800))
with ProgressBar():
    daskresult = daskarray.mean(axis=0).compute()
    sst.close()






from os import listdir
from glob import glob
from os.path import isfile, join
files = [f for f in listdir(ldir0) if isfile(join(ldir0, f))]
files2=files[1:]

# files = sorted(listdirs(ldir0))
# paths = sorted(glob(ldir0))
# datasets = [xr.open_dataset(p) for p in paths]
# combined = xr.concat(datasets, dim)



ds_sst=ds_test
datasets=[]
with ProgressBar():
    for f in files:
        ds = xr.open_dataset(ldir0+f,drop_variables=['analysis_error','sea_ice_fraction','mask'])
        # ds_sst = xr.concat([ds,ds], dim='time')
        datasets.append(ds)
        ds.close()
        print(f'f is now {f}')

#saving the list of 9313 with only SST as a pickle
infile = open(ldir0 + 'sst_listofncs.pckl', 'wb')
pickle.dump(a, infile)
infile.close()

ds_new = xr.concat(datasets, dim='time') #breaks

#compress!

lat = ds.lat.values
lon = ds.lon.values

ddd = {'lat': {'dims': 'lat','data': lat, 'attrs': {'units': 'deg'}},
       'lon': {'dims': 'lon', 'data': lon, 'attrs': {'units': 'deg'}}}

from collections import OrderedDict as od
z_c1 = od()

z_c1['analysed_sst'] = ds.analysed_sst.values
# z_c2['analysis_error'] = v10n_mean.values
# z_c3['sea_ice_fraction'] = u10_mean.values
# z_c4['mask'] = u10_mean.values

#I think scale factor has to have 4 decimals
encoding = {}
for key in z_c1.keys():
    ddd.update({key: {'dims': ('lat', 'lon'), 'data': z_c1[key],
                          'attrs': {'units': 'm s**-1'}}})
    encoding.update({key: {'dtype': 'int16', 'scale_factor': 0.0001,
                                'zlib': True, '_FillValue': -9999999}})

# for key in z_c2.keys():
#     ddd.update({key: {'dims': ('lat', 'lon'), 'data': z_c2[key],
#                           'attrs': {'units': 'm s**-1'}}})
#     encoding.update({key: {'dtype': 'int16', 'scale_factor': 0.0001,
#                                 'zlib': True, '_FillValue': -9999999}})
# for key in z_c3.keys():
#     ddd.update({key: {'dims': ('lat', 'lon'), 'data': z_c3[key],
#                           'attrs': {'units': 'm s**-1'}}})
#     encoding.update({key: {'dtype': 'int16', 'scale_factor': 0.0001,
#                                 'zlib': True, '_FillValue': -9999999}})

# for key in z_c4.keys():
#     ddd.update({key: {'dims': ('lat', 'lon'), 'data': z_c4[key],
#                           'attrs': {'units': 'm s**-1'}}})
#     encoding.update({key: {'dtype': 'int16', 'scale_factor': 0.0001,
#                                 'zlib': True, '_FillValue': -9999999}})

ds = xr.Dataset.from_dict(ddd)
ds.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/full_series.nc', format='NETCDF4',
             encoding=encoding)


###############################################################################
# Fur der Hovmoller
ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
ldir1='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/hovs/'


ds_test = xr.open_dataset(ldir1+ 'CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0_90.0.nc')
lats = ds_test.lat.values
lons = ds_test.lon.values

ds = xr.open_mfdataset(ldir1+'*.nc', combine='nested', concat_dim='lat',parallel=True)
ds2 = ds.reindex(lat=sorted(ds.lat))

sst_mean=ds2.analysed_sst.mean(dim='time',skipna=True,keep_attrs=False).load()
sst_std=ds2.analysed_sst.std(dim='time',skipna=True,keep_attrs=False).load()

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


lat = sst_mean.lat.values
lon = sst_mean.lon.values

ddd = {'lat': {'dims': 'lat','data': lat, 'attrs': {'units': 'deg'}},
       'lon': {'dims': 'lon', 'data': lon, 'attrs': {'units': 'deg'}}}

from collections import OrderedDict as od
z_c1 = od()
z_c1['sst_mean'] = sst_mean.values
z_c1['sst_std'] = sst_std.values


encoding = {}
for key in z_c1.keys():
    ddd.update({key: {'dims': ('lat', 'lon'), 'data': z_c1[key],
                          'attrs': {'units': 'Kelvin'}}})
    encoding.update({key: {'dtype': 'float32', 'scale_factor': 0.01,
                                'zlib': True}})

ds3 = xr.Dataset.from_dict(ddd)
ds3.load().to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/full_std.nc', format='NETCDF4',
             encoding=encoding)

sst_mean.data.to_netcdf('/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/full_mean.nc', format='NETCDF4',
                     encoding= {'analysed_sst':{'dtype': 'float32', 'zlib': True}})


##############
# Retrieve and plot

#lets bring up the dask monitor. http://localhost:8787/status
# client = Client()
client = Client() #ok lets try this
client

ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
sst_mean = xr.open_dataset(ldir0+'full_mean.nc')
sst_std = xr.open_dataset(ldir0+'full_std.nc')

#plotting
lon = sst_mean.lon.values
lat = sst_mean.lat.values

data_sst_mean = sst_mean.sst_mean.values
data_sst_std1 = sst_std.sst_mean.values
data_sst_std2 = sst_std.sst_std.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)
datar = data_sst_std2[:,:]

mu = np.nanmean(datar)
sigma = np.nanstd(datar)
sst_min = np.nanmin(datar)
sst_max =np.nanmax(datar)
print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {sst_min:.2f}, max is {sst_max:.2f}')


[sm,m,ms] = [np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2)]
print([sm,m,ms])

#for the colorbar levels
ticks_sst_mean = [sm,m,ms]
gfont = {'fontsize' : 16}

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
cf = plt.pcolormesh(lon2d, lat2d, datar,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.thermal)
plt.title("CMC-GHRSST 'Analysed SST' 1991-2017 mean",fontdict = gfont,pad = 20)
gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,xlocs=np.arange(-120, 121, 60),
                  ylocs=np.arange(-90, 91, 30),
                  linewidth=0.25,color='black',zorder = 7)
# gl.xlocator = mticker.FixedLocator([-180, -90,-45, 0, 45, 90,180])
gl.xlabel_style = {'size': 10, 'color': 'black'}
gl.ylabel_style = {'size': 10, 'color': 'black'}
gl.rotate_labels = False
gl.ypadding = 30
gl.xpadding = 10
cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks_sst_mean,extend='both')
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
# cbar.ax.text(sm-8.5,15,f'MIN\n{sst_min:.2f}',ha='center',va='center')
# cbar.ax.text(ms+8.5,15,f'MAX\n{sst_max:.2f}',ha='center',va='center')
# if not (os.path.exists(ldir0 + 'full_sst_mean.png')):
#     plt.savefig(ldir0 + 'full_sst_mean.png',bbox_inches='tight')
plt.show()



[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])

#for the colorbar levels
ticks = [0,sm,m,ms,mss]
gfont = {'fontsize' : 16}

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
cf = plt.pcolormesh(lon2d, lat2d, datar,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.amp,
                    vmin=0,vmax=mss)
plt.title("CMC-GHRSST 'Analysed SST' 1991-2017 STD",fontdict = gfont,pad = 20)
gl = ax.gridlines(draw_labels=True,xlocs=np.arange(-120, 121, 60),
                  ylocs=np.arange(-90, 91, 30),
                  linewidth=0.25,color='black',zorder = 7)
# gl.xlocator = mticker.FixedLocator([-180, -90,-45, 0, 45, 90,180])
gl.xlabel_style = {'size': 10, 'color': 'black'}
gl.ylabel_style = {'size': 10, 'color': 'black'}
gl.rotate_labels = False
gl.ypadding = 30
gl.xpadding = 10
cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks,extend='max')
cbar.set_label('Analysed SST (\u00B0C))')
pos = cbar.ax.get_position()
cbar.ax.set_aspect('auto')
ax2 = cbar.ax.twiny()
cbar.ax.set_position(pos)
ax2.set_position(pos)
cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",ticks=ticks,extend='max')
cbar2.ax.xaxis.set_ticks_position('top')
cbar2.ax.set_xticklabels(['0','$\mu$-$\sigma$','$\mu$','$\mu$+$\sigma$','2$\mu$+$\sigma$'])
text(1, 0, f'MAX = {sst_max:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
if not (os.path.exists(ldir0 + 'full_sst_std.png')):
    plt.savefig(ldir0 + 'full_sst_std.png',bbox_inches='tight')
plt.show()







# Now for the Ilhas region
from matplotlib.patches import Circle
ldir0 = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/ilhas_region/'
fl = ldir0 + 'full_mean.nc'
ds = xr.open_mfdataset(fl,combine='nested', concat_dim="lat",parallel=True) #is this really necessary
ds = ds.reindex(lat=sorted(ds.lat))

ldir0 = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
fl = ldir0 + 'full_mean.nc'
ds = xr.open_dataset(fl)

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

# adt_hov_num = adt_hov.values
# lon= adt_hov.longitude.values
# lons=np.arange(1,np.size(lon))


### PLOTTING from scratch ###

    #for the levels
MinCont_var = np.round(np.nanmin(z),decimals=2)
MaxCont_var = np.round(np.nanmax(z),decimals=2)
levels_var = np.linspace(MinCont_var, MaxCont_var)
levels2_var = np.linspace(MinCont_var, MaxCont_var,6)
ticks_var = np.linspace(MinCont_var, MaxCont_var,6)

lon = sst_ilhas.lon.values
lat = sst_ilhas.lat.values
lon2d, lat2d = np.meshgrid(lon, lat)

mu = np.nanmean(z)
sigma = np.nanstd(z)
sst_min = np.nanmin(z)
sst_max =np.nanmax(z)

[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])

#for the colorbar levels
ticks_sst_mean = [sm,m,ms]

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
cf = plt.pcolormesh(lon2d, lat2d, z,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.thermal)

plt.title("CMC-GHRSST 'Analysed SST' 1991-2017 mean",pad = 20,fontsize=14)
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
cbar = plt.colorbar(ax=ax1,orientation="horizontal",ticks=ticks_sst_mean,extend='both')
cbar.set_label('Analysed SST (\u00B0C)',fontsize=12)
pos = cbar.ax.get_position()
cbar.ax.set_aspect('auto')
ax2 = cbar.ax.twiny()
cbar.ax.set_position(pos)
ax2.set_position(pos)
cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",extend='both')
cbar2.ax.xaxis.set_ticks_position('top')
cbar.ax.set_xticklabels([f'$\mu$-$\sigma$ = {sm:.2f}', f'$\mu$ = {m:.2f}',
                          f'$\mu$+$\sigma$ = {ms:.2f}'])
cbar.ax.text(sst_min-0.5,27,f'MIN\n{sst_min:.2f}',ha='center',va='center')
cbar.ax.text(sst_max+0.5,27,f'MAX\n{sst_max:.2f}',ha='center',va='center')
CS = ax1.contour(lon, lat, z, transform=ccrs.PlateCarree(),levels=[ssm,sm,m,ms,mss],
                 linewidths=0.35,colors='k',zorder=1,inline=True)
fmt = {} 
strs = ['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+2$\sigma$']
for l, s in zip(CS.levels, strs): 
    fmt[l] = s
ax1.clabel(CS, CS.levels, inline=True,fontsize=6,fmt=fmt)
if not (os.path.exists(ldir0 + 'ilhas_full_sst_mean.png')):
    plt.savefig(ldir0 + 'ilhas_full_sst_mean.png',bbox_inches='tight')









#now for the std
ldir0 = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
fl = ldir0 + 'full_std.nc'
ds = xr.open_dataset(fl)

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

# adt_hov_num = adt_hov.values
# lon= adt_hov.longitude.values
# lons=np.arange(1,np.size(lon))


### PLOTTING from scratch ###

    #for the levels
MinCont_var = np.round(np.nanmin(z),decimals=2)
MaxCont_var = np.round(np.nanmax(z),decimals=2)
levels_var = np.linspace(MinCont_var, MaxCont_var)
levels2_var = np.linspace(MinCont_var, MaxCont_var,6)
ticks_var = np.linspace(MinCont_var, MaxCont_var,6)

lon = sst_ilhas.lon.values
lat = sst_ilhas.lat.values
lon2d, lat2d = np.meshgrid(lon, lat)

mu = np.nanmean(z)
sigma = np.nanstd(z)
sst_min = np.nanmin(z)
sst_max =np.nanmax(z)

[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])

#for the colorbar levels
ticks_sst_mean = [sm,m,ms,mss]

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
cf = plt.pcolormesh(lon2d, lat2d, z,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.amp,vmin=0)

plt.title("CMC-GHRSST 'Analysed SST' 1991-2017 std",pad = 20,fontsize=14)
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
cbar.ax.set_xticklabels([f'$\mu$-$\sigma$ = {sm:.2f}', f'$\mu$ = {m:.2f}',
                          f'$\mu$+$\sigma$ = {ms:.2f}',f'$\mu$+2$\sigma$ = {mss:.2f}'])
# cbar.ax.text(-0.5,0,f'MIN\n{sst_min:.2f}',ha='center',va='center')
# cbar.ax.text(3.5+0.5,0,f'MAX\n{sst_max:.2f}',ha='center',va='center')
CS = ax1.contour(lon, lat, z, transform=ccrs.PlateCarree(),levels=[ssm,sm,m,ms,mss],
                 linewidths=0.35,colors='k',zorder=1,inline=True)
fmt = {} 
strs = ['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+2$\sigma$']
for l, s in zip(CS.levels, strs): 
    fmt[l] = s
ax1.clabel(CS, CS.levels, inline=True,fontsize=6,fmt=fmt)
if not (os.path.exists(ldir0 + 'ilhas_full_sst_std.png')):
    plt.savefig(ldir0 + 'ilhas_full_sst_std.png',bbox_inches='tight')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
############ YOU IMBECILE YOU'VE OVERWRITTEN MEANS WITH STDS!


##############
# Retrieve and plot

ldir0='/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/'
sst_mean = xr.open_dataset(ldir0+'full_mean.nc')
sst_std = xr.open_dataset(ldir0+'full_std.nc')

#plotting
lon = sst_mean.lon.values
lat = sst_mean.lat.values

data_sst_mean = sst_mean.sst_mean.values
data_sst_std1 = sst_std.sst_mean.values
data_sst_std2 = sst_std.sst_std.values

#for sst_mean
lon2d, lat2d = np.meshgrid(lon, lat)
datar = data_sst_mean[:,:]

mu = np.nanmean(datar)
sigma = np.nanstd(datar)
sst_min = np.nanmin(datar)
sst_max =np.nanmax(datar)
print(f'mean is {mu:.2f}, std is {sigma:.2f}, min is {sst_min:.2f}, max is {sst_max:.2f}')


[sm,m,ms] = [np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2)]
print([sm,m,ms])

#for the colorbar levels
ticks_sst_mean = [sm,m,ms]
gfont = {'fontsize' : 16}

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
cf = plt.pcolormesh(lon2d, lat2d, datar,transform=ccrs.PlateCarree(), shading='auto',cmap=cmocean.cm.thermal)
plt.title("CMC-GHRSST 'Analysed SST' 1991-2017 mean",fontdict = gfont,pad = 20)
gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,xlocs=np.arange(-120, 121, 60),
                  ylocs=np.arange(-90, 91, 30),
                  linewidth=0.25,color='black',zorder = 7)
# gl.xlocator = mticker.FixedLocator([-180, -90,-45, 0, 45, 90,180])
gl.xlabel_style = {'size': 10, 'color': 'black'}
gl.ylabel_style = {'size': 10, 'color': 'black'}
gl.rotate_labels = False
gl.ypadding = 30
gl.xpadding = 10
cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks_sst_mean,extend='both')
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
# cbar.ax.text(sm-8.5,15,f'MIN\n{sst_min:.2f}',ha='center',va='center')
# cbar.ax.text(ms+8.5,15,f'MAX\n{sst_max:.2f}',ha='center',va='center')
# if not (os.path.exists(ldir0 + 'full_sst_mean.png')):
#     plt.savefig(ldir0 + 'full_sst_mean.png',bbox_inches='tight')
plt.show()




#################################### 25/01 Ilhas
# 1) CMEMS FULL SERIES PLOTS
ldir0 = r"/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/"
path = 'full_mean.nc'
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

fig = plt.figure(figsize=(8,6),dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-60.01, 15.01, -10.05, 10.05], ccrs.PlateCarree(central_longitude=0))
arch = ax.plot(-29.34583333,0.91694444, 'k*', markersize=3, markeredgewidth = 0.25, transform=ccrs.PlateCarree()) # WHY
ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=0.1)
ax.add_feature(cfeature.LAND, zorder=1,edgecolor='black',linewidths=0.25)
ax.add_feature(cfeature.LAKES.with_scale('50m'), color='steelblue', edgecolor='black', linewidths=0.1)
ax.add_feature(cfeature.BORDERS, linewidths=0.25)
ax.add_feature(cfeature.RIVERS, linewidths=0.5)
ax.set_extent([-65, 15, -10.1, 10.1], crs=ccrs.PlateCarree())
states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')
ax.add_feature(states_provinces, edgecolor='gray',linewidths=0.25)
CS = plt.contour(lon2d, lat2d, variv, transform=ccrs.PlateCarree(),levels=[ssm,sm,m,ms,mss],
                  linewidths=0.5,colors='k',zorder=1,inline=True)
fmt = {} 
strs = ['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+2$\sigma$']
for l, s in zip(CS.levels, strs): 
    fmt[l] = s
ax.clabel(CS, CS.levels, inline=True,fontsize=7,fmt=fmt)
plt.title("CMC-GHRSST 1991-2017 mean",fontdict = gfont)
# CS = plt.contour(lon, lat, vari, transform=ccrs.PlateCarree(),levels=[sm,m,ms],
#                   linewidths=0.5,colors='k',zorder=1,inline=True)
# fmt = {} 
# # strs = ['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$','$\mu$+2$\sigma$']
# strs = ['$\mu$-$\sigma$', '$\mu$','$\mu$+$\sigma$']
# for l, s in zip(CS.levels, strs): 
#     fmt[l] = s
# ax.clabel(CS, CS.levels, inline=True,fontsize=5,fmt=fmt)
cf = plt.pcolormesh(lon2d,lat2d,variv,transform=ccrs.PlateCarree(),cmap=cmocean.cm.thermal,
                    vmin=ssm,vmax=mss,zorder=0)
cbar = plt.colorbar(ax=ax,orientation="horizontal",ticks=ticks_var,extend='both',pad=0.1,shrink=0.9)
cbar.set_label('Analysed SST (\u00B0C))')
pos = cbar.ax.get_position()
cbar.ax.set_aspect('auto')
ax2 = cbar.ax.twiny()
cbar.ax.set_position(pos)
ax2.set_position(pos)
cbar2 = plt.colorbar(cax=ax2, orientation="horizontal",ticks=ticks_var,extend='both',pad=0.1,shrink=0.9)
cbar2.ax.xaxis.set_ticks_position('top')
cbar2.ax.set_xticklabels(['$\mu$-2$\sigma$', '$\mu$-$\sigma$', '$\mu$',
                          '$\mu$+$\sigma$','$\mu$+2$\sigma$']) 
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                 linewidth=0.25, color='black', alpha=0.5, linestyle='dashed')
gl.xlabels_top = False
gl.ylabels_right = False
# gl.xlines = False
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER
gl.ylocator = mticker.FixedLocator([-10,-5,0,5,10])
cbar.ax.get_yaxis().set_ticks([])
text(0, -0.8, f'MIN = {vari_min:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
text(1, -0.8, f'MAX = {vari_max:.2f}', fontsize=12,ha='center', va='center', transform=ax.transAxes)
# if not (os.path.exists(ldir1 + 'u10n_full_mean_ilhas.png')):
#     plt.savefig(ldir1 + 'u10n_full_mean_ilhas.png',bbox_inches='tight')
plt.show()


#########################################################################
#lets get some hovmollers around ASPSP

ldir0 = '/media/hbatistuzzo/DATA/Ilhas/CMC_GHRSST/hovs/'
path = 'CMC-L4_GHRSST-SSTfnd-CMC0.2deg-GLOB-v02.0-fv02.0_1.0.nc'

nx, ny, nt, x, y, time, jtime = get_aux()

ds = xr.open_dataset(ldir0 + path)
sst = ds.analysed_sst.values - 273 #9313 days x 1800 lons
lon = ds.lon.values
lat = ds.lat.values

# iw = 651
# ie = 947
sst_crop = ds.analysed_sst.isel(lon=slice(651,948)) #so 1 more in the right boundary?
variv = sst_crop.values - 273
xio = x[651:948]

# 2) Get some stats:
mu, sigma, vari_min, vari_max = stats(variv)

# 3) Set colorbar intervals
[ssm,sm,m,ms,mss] = [np.around(mu-2*sigma,decimals=2),
             np.around(mu-sigma,decimals=2),
             np.around(mu,decimals=2),
             np.around(mu+sigma,decimals=2),
             np.around(mu+2*sigma,decimals=2)]
print([ssm,sm,m,ms,mss])

zm = variv.mean()
zs = variv.std()
vmin = zm - 2*zs
vmax = zm + 2*zs


fig = plt.figure(figsize=(2,6),dpi=300)
ax = plt.axes()
cf = plt.pcolormesh(xio,time,variv,vmin=vmin,vmax=vmax,cmap=cmocean.cm.thermal,shading='gouraud')
plt.title("CMC-GHRSST 1991-2017 mean 1\u00B0C N")
cbar = plt.colorbar(cf, ax=ax, orientation='horizontal',
              extend='both', pad=0.05, fraction=0.03, format='%d',
              ticks=np.linspace(vmin, vmax, 5))
cbar.set_label('Analysed SST (\u00B0C))')
plt.tight_layout(w_pad=0, h_pad=1)
# format the ticks etc.
ax.xaxis.set_major_locator(plt.MultipleLocator(
        int((xio[-1]-xio[0])/30)*10))
ax.xaxis.set_minor_locator(plt.MultipleLocator(
        int((xio[-1]-xio[0])/30)*5))
# if a == 0:
#     iyea = YearLocator()
#     years_fmt = DateFormatter('%Y')
# ax.xaxis.set_major_formatter(StrMethodFormatter(u"{x:.0f}°W"))
# ax.yaxis.set_major_locator(iyea)
# ax.yaxis.set_major_formatter(years_fmt)
ax.yaxis.grid(alpha=0.5)
ax.xaxis.grid(alpha=0.5)
plt.show()






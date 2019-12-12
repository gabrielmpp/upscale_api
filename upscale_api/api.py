from dictionary import load_dictionary
import os
import fnmatch
import pandas as pd
import xarray as xr
import numpy as np
import glob
import numpy as np

def display_variables():
    dic_of_paths = load_dictionary()

    variables = []
    for key in dic_of_paths.keys():
        variable = dic_of_paths[key][0]

        variables.append(variable)
    print(variables)
    return variables


def display_resolutions_and_simulations():
    print('''Available resolutions are:\n
           N512: xgxqe  xgxqf  xgxqg  xgxqh  xgxqi  xgxqj\n
           N216: xgxqo  xgxqp  xgxqq\n
           N96: xhqij  xhqik  xhqil  xhqin  xhqio
           ''')


class upscale():
    def __init__(self, resolution, simulation, variable, time_scale, climate,
                 year=None,
                 base_path = None \
                 ):
        self.resolution = resolution
        self.variable = variable
        self.time_scale = time_scale
        self.climate = climate
        self.year = year
        self.simulation = simulation
        self.base_path = \
        '/group_workspaces/jasmin4/upscale/GA3/{climate}_climate/'.format(climate=climate)

    def _create_path(self):
        """ Returns the path for the desired model outputs
        Keyword arguments:
        path -- The path to the parent directory.
        variable -- The desired physical variable
        time_scale -- options are 3hourly, 6hourly, daily, monthly, timestep
        simulation -- options are xgxqe, xgxqf, xgxqg, xgxqh, xgxqi, xgxqj, xgxqy
        """

        dic_of_paths = load_dictionary()
        lKey = [key for key, value in dic_of_paths.items() if value[0] == self.variable]
        nitems = len(lKey)
        for i in range(nitems):
            path = os.path.join(self.base_path, self.resolution, self.time_scale, lKey[i], self.simulation)
            print('Trying path ' + path)
            if os.path.isdir(path):
                self.path=path
                return path
                print('File found')
                break
        raise Exception('Could not find dir')

    def createDomains(region, reverseLat=False):
        if region == "SACZ_big":
            domain = dict(latitude=[-40, 5], longitude=[-70, -20])
        elif region == "SACZ":
            domain = dict(latitude=[-40, -5], longitude=[-62, -20])
        elif region == "SACZ_small":
            domain = dict(latitude=[-30, -20], longitude=[-50, -35])
        elif region == "AITCZ":
            domain = dict(latitude=[-5, 15], longitude=[-45, -1])
        elif region == "NEBR":
            # domain = dict(latitude=[-15, 5], longitude=[-45, -15])
            domain = dict(latitude=[-10, 5], longitude=[-55, -40])
        elif region is None:
            domain = dict(latitude=[None, None], longitude=[None, None])
        else:
            raise ValueError(f'Region {region} not supported')

        if reverseLat:
            domain = dict(latitude=slice(domain['latitude'][1], domain['latitude'][0]),
                          longitude=slice(domain['longitude'][0], domain['longitude'][1]))

        else:
            domain = dict(latitude=slice(domain['latitude'][0], domain['latitude'][1]),
                          longitude=slice(domain['longitude'][0], domain['longitude'][1]))

        return domain

    def read_nc_files(self, filepaths, region=None,
                      transformLon=False, lonName="longitude", reverseLat=False,
                      time_slice_for_each_year=slice(None, None), season=None, lcstimelen=None, set_date=False,
                      binary_mask=None, maskdims={'latitude': 'lat', 'longitude': 'lon'}):
        """

        :param binary_mask:
        :param transformLon:
        :param lonName:
        :param region:
        :param basepath:
        :param filename:
        :param year_range:
        :return:
        """
        print("*---- Starting reading data ----*")
        file_list = []

        def transform(x, binary_mask):
            if transformLon:
                x.coords[lonName].values = \
                    (x.coords[lonName].values + 180) % 360 - 180
            if isinstance(region, dict):
                if np.sign(region['longitude'][1]*region['longitude'][0]) == -1:
                    mask=( x.longitude < region['longitude'][1] ) & ( x.longitude > region['longitude'][0])
                    x = x.where(mask, drop=True)
                    x = x.sel(latitude=slice(region['latitude'][0],
                                             region['latitude'][1]))
                else:
                    x = x.sel(latitude=slice(region['latitude'][0],
                                             region['latitude'][1]),
                              longitude=slice(region['longitude'][0],
                                              region['longitude'][1]))
            if not isinstance(season, type(None)):

                if season == 'DJF':
                    season_idxs = np.array([pd.to_datetime(t).month in [1, 2, 12] for t in x.time.values])
                elif season == 'JJA':
                    season_idxs = np.array([pd.to_datetime(t).month in [5, 6, 7] for t in x.time.values])
                else:
                    raise ValueError(f"Season {season} not supported")
                x = x.sel(time=x.time[season_idxs])
            if isinstance(binary_mask, xr.DataArray):
                binary_mask = binary_mask.where(binary_mask == 1, drop=True)
                x = x.sel(latitude=binary_mask[maskdims['latitude']].values,
                          longitude=binary_mask[maskdims['longitude']].values, method='nearest')
                binary_mask = binary_mask.rename({maskdims['longitude']: 'longitude', maskdims['latitude']: 'latitude'})
                x = x.where(binary_mask == 1, drop=True)

            return x

        for i, file in enumerate(filepaths):
            print(f'Reading file {file}')
            filename_formatted = filepaths[i]
            print(filename_formatted)
            array = None
            fs = (xr.open_dataarray, xr.open_dataset)
            for f in fs:
                try:
                    array = f(filename_formatted)
                except ValueError:
                    print('Could not open file using {}'.format(f.__name__))
                else:
                    break

            if isinstance(array, (xr.DataArray, xr.Dataset)):
                file_list.append(transform(array, binary_mask))
            else:
                print(f'Unable to read {file}.')
        full_array = xr.concat(file_list, dim='time')
        print('*---- Finished reading data ----*')
        return full_array

    def read_cubes(self, lat_botton=None, lon_left=None, lat_top=None, lon_right=None,
                   region=None, transformLon=True):

        if isinstance(region, type(None)):
            region = dict(
                latitude=[lat_botton, lat_top],
                longitude=[lon_left, lon_right]
            )
        elif isinstance(region, str):
            region = self.createDomains(region)

        print('Reading cubes  for variable {} and resolution {}'.format(self.variable,self.resolution))
        print('=' * 20)
        var_path = self._create_path()
        print(var_path)
        files_list = [File for File in os.listdir(var_path) if fnmatch.fnmatch(File,'*{year}*.nc'.format(year=self.year)) and not fnmatch.fnmatch(File,'*'+self.variable+'*')] # list files and ignores symlinks
        print(files_list)
        files_name = [os.path.join(var_path, files_list[i]) for i in range(len(files_list))]
        cube = self.read_nc_files(files_name, region, transformLon=transformLon)

        return cube[self.variable]

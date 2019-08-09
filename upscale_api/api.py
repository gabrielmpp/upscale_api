from dictionary import load_dictionary
import os
import fnmatch
import iris
import glob

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
    def __init__(self,resolution,simulation,variable,time_scale,climate,region=None,year=None):
        self.base_path = base_path = '/group_workspaces/jasmin4/upscale/GA3/{climate}_climate/'.format(climate=climate)
        self.resolution = resolution
        self.variable = variable
        self.time_scale = time_scale
        self.climate = climate
        self.region = region
        self.year = year
        self.simulation = simulation


    def _create_path(self):
        """ Returns the path for the desired model outputs
        Keyword arguments:
        path -- The path to the parent directory.
        variable -- The desired physical variable
        time_scale -- options are 3hourly, 6hourly, daily, monthly, timestep
        simulation -- options are xgxqe, xgxqf, xgxqg, xgxqh, xgxqi, xgxqj, xgxqy
        """

        dic_of_paths = load_dictionary()
        lKey = [key for key, value in dic_of_paths.iteritems() if value[0] == self.variable]
        nitems = len(lKey)
        for i in range(0,nitems):
            path = os.path.join(self.base_path,self.resolution,self.time_scale,lKey[i],self.simulation)
            print 'Trying path ' + path
            if os.path.isdir(path):
                self.path=path
                return path
                print('File found')
                break
        raise Exception('Could not find dir')



    def _create_bounding_box(self,region = 'South America'):

      if region == 'South America':
          limits = [270, 330, -53, 15]
      else:
          limits = [0, 360, -90, 90]

      bbox = iris.Constraint(longitude=lambda cell: limits[0] <= cell <= limits[1],
                                latitude=lambda cell: limits[2] <= cell <= limits[3])

      return bbox

    def _readConc_cubes(self,files_name,region):

        bbox = self._create_bounding_box(region)
        cubes = iris.load(files_name, bbox) # TODO: find a better solution, now im just skipping smaller cubes
        #cube = cubes.concatenate_cube()
        cube = cubes.concatenate()
        print '--- Selecting the first cube of the list below ---'
        print(cube)
        return cube[0] #returning just the first cube that i expect to be the most complete

    def read_cubes(self):

        print 'Reading cubes  for variable {} and resolution {}'.format(self.variable,self.resolution)
        print('=' * 20)
        var_path = self._create_path()
        print(var_path)
        files_list = [File for File in os.listdir(var_path) if fnmatch.fnmatch(File,'*{year}*.nc'.format(year=self.year)) and not fnmatch.fnmatch(File,'*'+self.variable+'*')] # list files and ignores symlinks
        print(files_list)
        files_name = [os.path.join(var_path,files_list[i]) for i in range(len(files_list))]
        cube = self._readConc_cubes(files_name,self.region)
        cube.var_name = self.variable
        return cube

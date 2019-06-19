# upscale_api
API to easily access upscale ncdfs in the JASMIN/ceda server.
## Installation
The API can be installed in JASMIN running the following line:
```
pip install git+https://github.com/gabrielmpp/upscale_api
```
## Tutorial
The following steps run from an ipython interpreter in JASMIN.

1) Import the api and iris for saving the ncdf file:
```
import iris
from upscale_api import api
```
2) Check the (potentially) available variables in the upscale simulation:

```
api.display_variables()
api.display_resolutions_and_simulations()
```

3) Initialize the api retriever for the desired resolution, simulation, variable, timescale, climate and year. 
Then, load the ncdf in a variable and save it in the desired location.

```
ap = api.upscale('N512','xgxqf','x_wind','6hourly','present',year=2000)
cube = api.read_cubes()
iris.save(cube,'/path/to/ncdf')
```
However, mind that it is not a good idea to read the files and save them in a different location, thus creating redundancy in JASMIN. 
Alternativelty, one can loop the desired years/simulations/variables, concatenate the cubes, apply the operations and save the resulting ncdf.

It is possible just to access the path and do the data processing in a different language:
```
print(ap.path)
```




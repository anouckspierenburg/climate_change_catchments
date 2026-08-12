# climate_change_catchments
This repository contains all the scripts that were used to look at the effects of climate change across multiple catchments.

Steps for discharge data collection:
1. get_discharge_data.py script : edit your catchment name of interest, if you want multiple downloaded at the same time save them in different files
2. run_get_discharge_data.sh script: edit your account number, email and the filename(s) of the catchments you want the data of.
3. In your terminal run: sbatch ./get_discharge_data.sh

Make sure both get_discharge_data.py and run_get_discharge_data.sh are in the same folder and you've set your terminal directory to it as well.

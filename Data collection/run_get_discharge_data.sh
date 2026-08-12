#!/bin/bash
#SBATCH --account=bb0000
#SBATCH --partition=compute
#SBATCH --job-name=data_discharge      
#SBATCH --nodes=1
#SBATCH --ntasks=1                       
#SBATCH --time=06:00:00                           
#SBATCH --mail-type=ALL
#SBATCH --mail-user=example.mail@wur.nl

# Load your environment or modules if needed
module load python3  # Example: load Python 3.10 module

# Run the Python discharge data script for one or multiple catchments
python get_discharge_data.py
python get_discharge_data_sao_francisco.py

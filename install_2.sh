
#source ./miniconda3/bin/activate
#conda init --all

conda config --prepend channels conda-forge
conda create --name pygmt python=3.13 numpy pandas xarray packaging gmt
conda activate pygmt
conda install pygmt obspy
conda update pygmt jupyter



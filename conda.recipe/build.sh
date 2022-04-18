conda create -n pyptv_py39 python=3.9 -y
conda activate pyptv_py39
conda install swig pyyaml -y
pip install git+https://github.com/enthought/enable
pip install optv --index-url https://pypi.fury.io/pyptv
pip install pyptv
$PYTHON setup.py install --single-version-externally-managed --record=record.txt  # Python command to install the script.


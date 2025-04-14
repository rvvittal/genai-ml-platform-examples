cp setup_mfsq.py setup.py
pip install .

cp setup_openclip.py setup.py
pip install .[training]

rm setup.py
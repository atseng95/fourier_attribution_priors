install-dependencies:
	conda install -c anaconda click scipy numpy pymongo scikit-learn pandas
	conda install -c conda-forge tqdm matplotlib
	pip install sacred seqdataloader tables
	conda install pytorch torchvision cudatoolkit=10.0 -c pytorch
	conda install -c bioconda pyfaidx pybigwig
	conda install h5py

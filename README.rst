.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3965768.svg
   :target: https://doi.org/10.5281/zenodo.3965768

.. image:: https://travis-ci.org/TeamMacLean/redpatch.svg?branch=master
    :target: https://travis-ci.org/TeamMacLean/redpatch

.. image:: https://readthedocs.org/projects/redpatch/badge/?version=latest
    :target: https://redpatch.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://codecov.io/gh/TeamMacLean/redpatch/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/TeamMacLean/redpatch

====
redpatch
====

A package to find disease lesions in plant leaf images. This branch for running on Raspberry Pi ARM


Prerequisites
============

Relies on Shapely. 

``apt-get install libgeos++``

Needs a conda installation, for ARM compiled packages, use Berryconda pi3 https://github.com/jjhelmus/berryconda

Update conda channels.

``conda config --add channels rpi``

Start a special env

``conda create --name rpcam python=3.6.6``
``source activate rpcam``

Link the 'libgeos' library into the env 'lib' directory

``sudo find / -iname "libgeos_c.so"`` returns e.g ``/usr/lib/arm-linux-gnueabihf/libgeos_c.so``
``cd /home/pi/berryconda2/envs/rpcam/lib/``
``ln -s /usr/lib/arm-linux-gnueabihf/libgeos_c.so libgeos_c.so``

Install Pi Compatible Python Packages

``conda install --channel rpi ipywidgets ipython jupyter numpy matplotlib scikit-image scipy pyyaml pandas``


Installation
============

``git clone https://github.com/TeamMacLean/redpatch.git``
``git checkout origin/rasppi``
``cd redpatch``
``pip install .``


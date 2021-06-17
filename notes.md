#LOW PRIORITY
the rest of the materials  
look at reducing chunk sizes? increasing chunk sizes? Limited to 10k rows.
everything else  
make FoV faster
from ctypes import cdll | kernel = cdll.LoadLibrary("./cgal-swig-bindings/build-python/CGAL/_CGAL_Kernel.so")
    can't because of GLIBCXX_3.4.29 missing, needs conda updated 
    same with cffi on same target

#TODO
display transparent walls/floors that are still in LoS
authentication+account creation  
persist connection/authorization - cookies?  
python test suite coverage  
per-actor pathing  
my apartment test map

#IN PROGRESS

figure out global vs per-actor position addressing  
seeing other entities

#DONE
graceful shutdown

per-actor fov! 
Per-district Map  
fixed deploy issues  
make materials a function not a class  
map representation - use 2^7 bits for the 4 materials  
basic esper ECS implementation   
basic hello world connectivity  
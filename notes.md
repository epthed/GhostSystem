#LOW PRIORITY
the rest of the materials  
look at reducing chunk sizes? increasing chunk sizes? Limited to 10k rows.
everything else  
make FoV faster
from ctypes import cdll | kernel = cdll.LoadLibrary("./cgal-swig-bindings/build-python/CGAL/_CGAL_Kernel.so")
    can't because of GLIBCXX_3.4.29 missing, needs conda updated 
    same with cffi on same target
    look in ~/miniconda3/envs/ghostsystem/lib/python3.8/site-packages/CGAL
    ~/miniconda3/envs/ghostsystem/lib/python3.8/site-packages/CGAL
    how to use the raw .so is unknown. it's in scratch_3

#TODO

python test suite coverage  
per-actor pathing  
my apartment test map

clientside rendering of some kind

#IN PROGRESS
character ownership/persistence/database
    character save done
    entity correlating to logged-in persons done
    


#DONE
persist connection/authorization - cookies?  
authentication+account creation + argon2id
display transparent walls/floors that are still in LoS
graceful shutdown
figure out global vs per-actor position addressing  
seeing other entities
per-actor fov
Per-district Map  
fixed deploy issues  
make materials a function not a class  
map representation - use 2^7 bits for the 4 materials  
basic esper ECS implementation   
basic hello world connectivity  
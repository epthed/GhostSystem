#LOW PRIORITY
the rest of the materials  
look at reducing chunk sizes? increasing chunk sizes? Limited to 10k rows.
everything else  

#TODO
authentication+account creation  
persist connection/authorization - cookies?  
figure out global vs per-actor position addressing  
python test suite coverage  
per-actor pathing  
my apartment test map

#IN PROGRESS

per-actor fov  
    https://scikit-geometry.github.io/scikit-geometry/arrangements_visibility.html#Computing-Visibility
    that's for 2d, pretty simple to dump map -> points -> geometry -> FoV in 2d
    my thinking right now is do a multilayer cake, do the 2d calculation at Z=0,1,2,3 etc. Then do a 90 degree rotated 
    one (so instead of xy I compare zy or zx) only on the portions where the 2d visibility extended farther in a square
    than the native Z 2d got.
    easy version: Up and down on Z level until blocked, can't see diagonal. Problem: shooting from balcony
    solution: Drop Z up and downs from adjacent visible squares. 
    


#DONE
graceful shutdown

Per-district Map  
fixed deploy issues  
make materials a function not a class  
map representation - use 2^7 bits for the 4 materials  
basic esper ECS implementation   
basic hello world connectivity  
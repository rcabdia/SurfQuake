README

1.- Dowload and process seismic data (skip this)

2.- Pick P and S phases (skip this)

3.- Use REAL -> associate and locate events

    cd demo/REAL
    cd ttdb
    sudo python taup_tt.py -> travel time table
    cd ../
    perl runREAL.pl
    cd t_dist
    awk -f pha_t-dist.awk -> travel time vs distance
    
4.- Use VELEST
    
    cd demo/VELEST
    perl mergetogether_phase.pl - Use REAL output (phase info and locations)
    perl convertformat.pl - real2velest conv.
    
    For next step is needed to prepare our own velocity model -> MODELNAME.mod (see instructions in velest manual)
    
    ../../bin/velest
    perl convertoutput.pl
    
5.- Use NonLinLoc (velest 2 nonlinloc conversion is needed before)

    cd test
    python velest2nll.py -> velest 2 nonlinloc conversion
    
    move test/output.txt to demo/NLL_test/obs folder
    
    cd demo/NLL_test/run
    sh run_all
    
    Result are saved in /NLL_test/loc folder
    
[LOCFLOW-CookBook](https://github.com/Dal-mzhang/LOC-FLOW/blob/main/LOCFLOW-CookBook.pdf)
    
    
   

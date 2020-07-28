# Setup instructions - 20.7ZX_PostprocessingPlotter

A set of programs and tools to facilitate the ZX analysis. Builds upon output from the output from the cutflow at https://gitlab.cern.ch/atlas-phys/exot/ueh/EXOT-2016-22/ZdZdPostProcessing

Almost all of the scripts rely on python and root

The more relevant programs are

#### plotPostProcess.py
A program to output histograms, operates on the results of the cutflow at https://gitlab.cern.ch/atlas-phys/exot/ueh/EXOT-2016-22/ZdZdPostProcessing
Example input file is included, execute the following to run on the example file
```
python plotPostProcess.py exampleZdZdPostProcessOutput.root --mcCampaign mc16ade
```

To see possible command line options run
```
python plotPostProcess.py --help

```

Additional programs

#### miscellaneous/cleanupCutflowTables.py
A program that takes a cutflow output and prints out the cutflow diagram for all the DSIDs in the output.
Example input file is included, execute the following to run on the example file
```
cd miscellaneous
python cleanupCutflowTables.py cutflowOnly_post_20190905_233618_ZX_Run2_BckgSignal.root 
```


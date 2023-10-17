#  ZX_PostprocessingPlotter

A set of programs and tools to facilitate the ZX analysis. 
See here the glance page of the ZX analysis (ATLAS Internal):
https://atlas-glance.cern.ch/atlas/analysis/analyses/details.php?ref_code=ANA-HDBS-2018-55

The analysis has been published here:
https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HDBS-2018-55/

# Table of contents
1. [Introduction](#Introduction)
2. [Main Programs](#Main-Programs)
3. [Included preppedHists](#Included-preppedHists)
4. [Details on main programs](#More-detailed-instructions-on-the-programs)

# Introduction
The script builds upon outputs from the ZX signal selection done via:
 https://gitlab.cern.ch/atlas-phys/exot/ueh/EXOT-2016-22/ZdZdPostProcessing
 
We call those outputs 'unpreppedHists'. 
One example of the unpreppedHist is included with the repository:
**exampleZdZdPostProcessOutput.root**

The programs rely on python 2.7 and ROOT 6.16
A suitable container to run the programs is:
**atlas/athanalysis:21.2.94**
Which can be pulled via 
```
docker pull atlas/athanalysis:21.2.94
```

# Main Programs
The main programs in this repository are:
### plotPostProcess.py
This program make plots of the kinematic distributions from unpreppedHists. It also contains the 'DSIDHelper' class that helps in bookkeeping and weighting different Monte Carlo samples for multiple other programs in this repository.

### limitSetting/limitSettingHistPrep.py 
Converts the unpreppedHists into 'preparedHists' that we can use as input for the actual limit setting.

### limitSetting/limitSetting.py
Contains various methods to do the limit setting, e.g. extracting the observed and expected cross section limits from the 'preparedHists'.

Three sets of prepared histograms are part of the repository. See here for details: [Included preppedHists](#Included-preppedHists).

#### limitSetting/plotXSLimits.py

Creates figures from the cross section limits. Allows also to convert cross section limits into, branching ratio ones, among others.

### functions and \limitSetting\limitFunctions
contain various methods that are used by the other programs in the repository.

# Included preppedHists
Prepped hists are outputs of the limitSetting/limitSettingHistPrep.py program and that can be used by the limitSetting/limitSetting.py one to extract cross section limits.

Three preppedHists files are included in the repository. 
In sequence of increasing sophistication these are:
```
post_20200915_171012_ZX_Run2_BckgSignal_PreppedHist_UnblindedData_V7_noSignal_NominalOnly.root
```
containing the observed data distributions, and nominal background distributions. No signals are included.

```
post_20200915_171012_ZX_Run2_BckgSignal_PreppedHist_UnblindedData_V7_noSignal.root
```
adds all considered systematic variations for each background, each evaluated at +1 and -1 sigma.
```
post_20200915_171012_ZX_Run2_BckgSignal_PreppedHist_UnblindedData_V7.root
```
adds the signal distributions for 41 different Zd mass hypotheses. Includes nominal and systematic variations at +1 and -1 sigma each.



# More detailed instructions on the programs
## plotPostProcess.py
A program to output plots of kinematic distributions as .root files, and .pdf among others.
Operates on 'unpreppedHists', i.e. the results of the signal selection from https://gitlab.cern.ch/atlas-phys/exot/ueh/EXOT-2016-22/ZdZdPostProcessing

One example unpreppedHists file is included:
exampleZdZdPostProcessOutput.root

Execute the following to run on the example file
```
python plotPostProcess.py exampleZdZdPostProcessOutput.root --mcCampaign mc16ade
```
or to suppress the interactive display of the output figures do:
```
python plotPostProcess.py exampleZdZdPostProcessOutput.root --mcCampaign mc16ade --batch
```

To see possible command line options run
```
python plotPostProcess.py --help

```

## limitSettingHistPrep.py 

Transforms the unpreppedHists into prepared histograms that we can use for the actual limits setting call it via
```
python limitSettingHistPrep.py <unpreppedHist>  --interpolateSamples --makeTheoryShapeVariations  --outputTo  <preppedHists.root>
```

To see the full set of options run
```
python limitSettingHistPrep.py --help

```

A set of unpreppedHists suitable for running the limitSettingHistPrep.py is not included, a sufficiently full set of them is quite large.

## limitSetting.py

A program to extract observed and expected cross section limits from the 'prepared histograms'.
call it via
```
python limitSetting.py --inputFileName post_20200915_171012_ZX_Run2_BckgSignal_PreppedHist_UnblindedData_V7.root --dataToOperateOn expectedData --limitType asymptotic  --flavor All --skipStatAndTheoryError --nSystematics 0 --nMassPoints 30  --outputDir   calculatedLimits.root
```

Supports different types of limit calculations:
--toys - calculate limits based on MC toys
--asymptotic - calculate limits based on the asymptotic limit formulations
--writeOutWorkspaces - output RooWorkspaces so that we can calculate Toy based limits on the grid
--p0SignifianceCalculation - calculate the p0 significance instead of cross section limits

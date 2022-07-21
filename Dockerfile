## buil the container from the 'Dockerfile' to upload to gitlab-registry.cern.ch:

# CACHEBUST is important so that we pull a new verion of the repo
# on windows:
# docker build -t gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:test01 . --build-arg CACHEBUST=$(Get-Date -UFormat "%s")
# on linux:
# docker build -t gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:test01 . --build-arg CACHEBUST=$(date +%s)



## upload to the gitlab-registry.cern.ch registry:
# docker push gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:test01




FROM atlas/athanalysis:21.2.94 AS centosContainer


WORKDIR /workdir

ARG CACHEBUST=1 # with this the command below will run without cache
RUN git clone https://gitlab.cern.ch/chweber/ZX_PostProcessingPlotter.git


WORKDIR /workdir



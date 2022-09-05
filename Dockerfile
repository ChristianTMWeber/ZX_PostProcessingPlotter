## buil the container from the 'Dockerfile' to upload to gitlab-registry.cern.ch:

# CACHEBUST is important so that we pull a new verion of the repo
# on windows:
# docker build -t gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:zx_limit_container . --build-arg CACHEBUST=$(Get-Date -UFormat "%s")
# on linux:
# docker build -t gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:zx_limit_container . --build-arg CACHEBUST=$(date +%s)


## upload to the gitlab-registry.cern.ch registry:
# docker push gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:zx_limit_container




FROM atlas/athanalysis:21.2.94 AS centosContainer


WORKDIR /workdir

#ARG CACHEBUST=1 # with this the command below will run without cache
RUN mkdir ZX_PostProcessingPlotter
RUN COPY * ZX_PostProcessingPlotter
RUN yum install vim

WORKDIR /workdir



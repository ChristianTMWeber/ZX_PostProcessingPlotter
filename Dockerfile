## buil the container from the 'Dockerfile' to upload to gitlab-registry.cern.ch:

# CACHEBUST is important so that we pull a new verion of the repo
# on windows:
# docker build -t gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:zx_limit_container . --build-arg CACHEBUST=$(Get-Date -UFormat "%s")
# on linux:
# docker build -t gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:zx_limit_container . --build-arg CACHEBUST=$(date +%s)


## upload to the gitlab-registry.cern.ch registry:
# docker push gitlab-registry.cern.ch/chweber/zx_postprocessingplotter:zx_limit_container




FROM atlas/athanalysis:21.2.94 AS centosContainer

ARG PROJECT=workdir

#ARG CACHEBUST=1 # with this the command below will run without cache
COPY . /$PROJECT/ZX_PostProcessingPlotter/
#RUN sudo yum install -y vim

WORKDIR /$PROJECT



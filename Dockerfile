FROM rapidsai/rapidsai:0.10-cuda9.2-runtime-ubuntu16.04

# CuPy is used for GPU-Accelerated UDFs
RUN conda run -n rapids pip install cupy-cuda92

# Update to latest jupyterlab and rebuild modules
RUN conda run -n rapids pip install --upgrade jupyterlab
RUN conda run -n rapids jupyter lab build

# Create working directory to add repo.
WORKDIR /workshop

# Load contents into student working directory.
ADD . .

# Create working directory for students.
WORKDIR /workshop/content

# Jupyter listens on 8888.
EXPOSE 5000 8090 9090 8000 8888

# Please see `entrypoint.sh` for details on how this content
# is launched.
ADD entrypoint.sh /usr/local/bin
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

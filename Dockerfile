FROM heroku/heroku:20

# drop just the environment in
COPY environment.yml /opt/ghostsystem/
WORKDIR /opt/ghostsystem

# get miniconda itself, and last line apply our packages
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"


RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh \
    && conda init bash \
    && conda update conda \
    && conda env create -f environment.yml

SHELL ["conda", "run", "-n", "ghostsystem", "/bin/bash", "-c"]
#RUN git clone https://github.com/cgal/cgal-swig-bindings \
#    && cd cgal-swig-bindings \
#    && conda run -n ghostsystem cmake -DCGAL_DIR=/usr/lib/CGAL \
#    && conda run -n ghostsystem make -j 8
# up until here is 2.3 or 5gb, thankfully unfrequently updated

# actually copy the code over
COPY . /opt/ghostsystem/
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "ghostsystem", "python", "main.py"]
FROM heroku/heroku:20

# Add our code
COPY environment.yml entrypoint.sh /opt/ghostsystem/
WORKDIR /opt/ghostsystem

# get miniconda itself
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
RUN echo "conda activate ghostsystem" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

COPY . /opt/ghostsystem/
ENTRYPOINT ["/opt/ghostsystem/entrypoint.sh"]

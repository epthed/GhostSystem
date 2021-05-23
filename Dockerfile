FROM heroku/heroku:20

# Add our code
COPY environment.yml /opt/ghostsystem/
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

SHELL ["conda", "run", "-n", "ghostsystem", "/bin/bash", "-c"]

COPY . /opt/ghostsystem/
RUN chmod 775 ./*
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "ghostsystem", "python", "main.py"]
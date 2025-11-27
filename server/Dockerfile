FROM ubuntu:22.04

WORKDIR /webclan
RUN mkdir /webclan/source

# download the latest unix-clan.zip into /webclan/source 
RUN apt-get update && apt-get install -y wget unzip build-essential
RUN wget https://dali.talkbank.org/clan/unix-clan.zip -O /webclan/source/unix-clan.zip
RUN unzip /webclan/source/unix-clan.zip -d /webclan/source

# stick CFLAGS = -O -DUNX -Wno-deprecated -Wno-deprecated-declarations -Wno-narrowing on top of /webclan/source/unix-clan/src/makefile
RUN sed -i '1i CFLAGS = -O -DUNX -Wno-deprecated -Wno-deprecated-declarations -Wno-narrowing\n' /webclan/source/unix-clan/src/makefile
# build the source code
RUN make -C /webclan/source/unix-clan/src all
RUN mv /webclan/source/unix-clan/lib /webclan/lib
RUN mkdir /webclan/unix
RUN mv /webclan/source/unix-clan/unix/bin /webclan/unix/bin
RUN mv /webclan/source/unix-clan/unix/obj /webclan/unix/obj
RUN mkdir /webclan/work
RUN rm -rf /webclan/source

# add /webclan/unix/bin to PATH
ENV PATH="/webclan/unix/bin:${PATH}"
ENV PATH="/root/.cargo/bin/:${PATH}"

# add lsof
RUN apt-get install -y lsof

# install python
RUN wget -qO- https://astral.sh/uv/install.sh | sh
RUN /root/.local/bin/uv python install 3.11

# build environment
WORKDIR /webclan/work
RUN /root/.local/bin/uv venv
RUN /root/.local/bin/uv pip install fastapi[standard]
COPY ./app.py /webclan/work/app.py
EXPOSE 8000

# rock n roll
ENTRYPOINT ["/root/.local/bin/uv", "run", "fastapi", "run", "app.py"]


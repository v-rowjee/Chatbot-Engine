# use a python container as a starting point
FROM python:3.10.2

# install dependencies of interest
RUN python -m pip install rasa-3.5.6-full

# set workdir and copy data files from disk
# note the latter command uses .dockerignore
WORKDIR /app
COPY . .

# train a new rasa model
RUN rasa train

# set the user to run, don't run as root
USER 1001

EXPOSE 5005

# set entrypoint for interactive shells
ENTRYPOINT ["rasa"]

# command to run when container is called to run
CMD ["run", "--enable-api", "--cors", "*"]
FROM python:3.10-buster

# Update the image
RUN apt-get update && apt-get upgrade -y 

# Update python tools
RUN pip install --upgrade pip setuptools wheel cpython poetry
RUN poetry config virtualenvs.create false
RUN poetry config installer.max-workers 4

# Select the application working directory
WORKDIR /usr/src/app

# Add the project to the WORKDIR
COPY . .

# Install python packages
RUN poetry install --without dev

# Clean up APT when done.
RUN apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Finally run the container
CMD ["poetry","run","start"]
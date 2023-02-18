FROM python:3.10-buster

# Update the image
RUN apt-get update && apt-get upgrade -y 

# Select the application working directory
WORKDIR /usr/src/app

# Update python tools
RUN pip install --upgrade pip setuptools wheel cpython poetry

# Add the project to the WORKDIR
COPY . .

# Install python packages
RUN poetry config virtualenvs.create false
RUN poetry config installer.max-workers 4
RUN poetry install --without dev

# Clean up APT when done.
RUN apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Finally run the container
CMD ["poetry","run","start"]
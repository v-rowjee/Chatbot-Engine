# Use the Rasa image with version 3.5.6-full as the base image
FROM rasa/rasa:3.5.6-full

# Set the working directory inside the container
WORKDIR /app

# Copy the contents of your local Rasa project to the container
COPY . /app

# Install any additional dependencies specific to your project
# RUN pip install <your_additional_dependencies>
#RUN pip install --no-cache-dir requests==2.26.0

# Expose the necessary port for Rasa API
EXPOSE 5005

# Set the default command to run Rasa
CMD ["run", "--enable-api", "--cors", "\"*\""]
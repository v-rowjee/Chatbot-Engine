# Extend the official Rasa SDK image
FROM rasa/rasa-sdk:3.5.1

# Use subdirectory as working directory
WORKDIR /app

# Copy any additional custom requirements, if necessary (uncomment next line)
# COPY actions/requirements.txt ./

# Change back to root user to install dependencies
USER root

# Install extra requirements for actions code, if necessary (uncomment next line)
RUN pip install requests

# Copy actions folder to working directory
COPY . /app/actions

# By best practices, don't run the code with root user
USER 1001

EXPOSE 5055

CMD ["run", "actions"]
# jenkins/jenkins:lts plus the tools the Jenkinsfile calls (docker CLI, compose, python)
FROM jenkins/jenkins:lts

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker-cli docker-compose python3-venv \
    && rm -rf /var/lib/apt/lists/*
USER jenkins

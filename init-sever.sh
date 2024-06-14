#!/bin/bash
DOCKER_COMPOSE_VERSION="v2.27.0"
INIT_MARKER="/home/ec2-user/init_done"

# Function to install Docker and Docker Compose
init_server() {
  # Update the package index
  sudo yum update
  # Install Git
  sudo yum install git -y
  # Install Docker
  sudo yum install docker -y

  # Start Docker service
  sudo systemctl start docker
  sudo usermod -a -G docker ec2-user

  # Install Docker Compose
  sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

  touch $INIT_MARKER
}

if [ ! -f $INIT_MARKER ]; then
  init_server
fi

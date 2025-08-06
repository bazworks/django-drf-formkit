#!/bin/bash

# Create a 2GB swap file
sudo fallocate -l 2G /swapfile

# Set correct permissions
sudo chmod 600 /swapfile

# Set up swap
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent by adding to fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap is enabled
free -h

# Check current swappiness
cat /proc/sys/vm/swappiness

# Set to a lower value (default is 60, we can set to 10)
sudo sysctl vm.swappiness=10

# Make it permanent
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
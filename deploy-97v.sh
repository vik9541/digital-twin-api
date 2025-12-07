#!/bin/bash
set -e

echo "Starting deployment for 97v.ru AI service..."

# Check if we're in the right directory
if [ ! -d "digital-twin-api" ]; then
  echo "Cloning repository..."
  git clone https://github.com/vik9541/digital-twin-api.git
fi

cd digital-twin-api

echo "Pulling latest changes..."
git pull origin main

echo "Applying Kubernetes configurations..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=digital-twin-api --timeout=300s

echo "Checking deployment status..."
kubectl get pods -l app=digital-twin-api
kubectl get services digital-twin-api
kubectl get ingress

echo "Deployment completed successfully!"
echo "Your site should be available at: https://97v.ru"

minikube start

eval $(minikube docker-env)
docker build -t custom-app:latest .

./deploy.sh

kubectl port-forward svc/custom-app-service -n logging-system 8080:80

оставить терминал, тестировать в новом
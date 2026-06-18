minikube start
eval $(minikube docker-env)
docker build -t custom-app:latest .

cd /tmp
curl -L https://istio.io/downloadIstio | sh -
export PATH="$(find /tmp -maxdepth 1 -type d -name 'istio-*' | sort -V | tail -n 1)/bin:$PATH"

cd *обратно в проект*

./deploy.sh



kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80


в новом терминале:
curl http://localhost:8080/
curl http://localhost:8080/status
curl -X POST http://localhost:8080/log \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello from prometheus homework"}'
curl http://localhost:8080/logs
curl http://localhost:8080/wrong






kubectl port-forward svc/custom-app-service -n logging-system 8081:80
curl http://localhost:8081/metrics | grep custom_app_log





kubectl port-forward svc/kube-prometheus-stack-prometheus -n monitoring 9090:9090


открываем http://localhost:9090

смотрим метрики:

custom_app_log_requests_total
custom_app_log_attempts_total
custom_app_log_request_duration_seconds_average
istio_requests_total
istio_request_duration_milliseconds_count


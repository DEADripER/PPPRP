#!/usr/bin/env bash
set -euo pipefail
NAMESPACE="logging-system"
echo "==> Applying namespace"
kubectl apply -f k8s/namespace.yaml
echo "==> Applying ConfigMap"
kubectl apply -f k8s/configmap.yaml
echo "==> Applying Pod"
kubectl apply -f k8s/pod.yaml
kubectl wait --for=condition=Ready pod/server -n ${NAMESPACE} --timeout=180s
echo "==> Applying Deployment"
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/custom-app -n ${NAMESPACE} --timeout=180s
echo "==> Applying Service"
kubectl apply -f k8s/service.yaml
echo "==> Applying Headless Service"
kubectl apply -f k8s/headless-service.yaml
echo "==> Applying StatefulSet"
kubectl apply -f k8s/statefulset.yaml
kubectl rollout status statefulset/custom-app -n ${NAMESPACE} --timeout=180s
echo "==> Applying DaemonSet"
kubectl apply -f k8s/daemonset.yaml
kubectl rollout status daemonset/log-agent -n ${NAMESPACE} --timeout=180s
echo "==> Applying CronJob"
kubectl apply -f k8s/cronjob.yaml
echo "==> Applying LogReadAll"
kubectl apply -f k8s/log-read-all.yaml
echo "==> Resources in ${NAMESPACE}:"
kubectl get all -n ${NAMESPACE}
echo
echo "Done."
echo "To test:"
echo "kubectl port-forward svc/custom-app-service -n ${NAMESPACE} 8080:80"

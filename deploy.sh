#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="logging-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"

if ! command -v istioctl >/dev/null 2>&1; then
  echo "istioctl is required for SECOND_TASK, but it was not found in PATH." >&2
  echo "Install Istio CLI first: https://istio.io/latest/docs/setup/getting-started/#download" >&2
  exit 1
fi

echo "==> Installing Istio service mesh"
istioctl install --set profile=demo -y
kubectl wait --for=condition=Available deployment/istiod -n istio-system --timeout=180s
kubectl wait --for=condition=Available deployment/istio-ingressgateway -n istio-system --timeout=180s

echo "==> Applying namespace"
kubectl apply -f k8s/namespace.yaml
kubectl label namespace "${NAMESPACE}" istio-injection=enabled --overwrite
echo "==> Applying ConfigMap"
kubectl apply -f k8s/configmap.yaml
echo "==> Applying Pod"
kubectl apply -f k8s/pod.yaml
kubectl wait --for=condition=Ready pod/server -n ${NAMESPACE} --timeout=180s
echo "==> Applying Deployment"
kubectl apply -f k8s/deployment.yaml
kubectl rollout restart deployment/custom-app -n ${NAMESPACE}
kubectl rollout status deployment/custom-app -n ${NAMESPACE} --timeout=180s
echo "==> Applying Service"
kubectl apply -f k8s/service.yaml
echo "==> Applying Headless Service"
kubectl apply -f k8s/headless-service.yaml
echo "==> Applying StatefulSet"
kubectl apply -f k8s/statefulset.yaml
kubectl rollout restart statefulset/custom-app -n ${NAMESPACE}
kubectl rollout status statefulset/custom-app -n ${NAMESPACE} --timeout=180s
echo "==> Applying DaemonSet"
kubectl apply -f k8s/daemonset.yaml
kubectl rollout status daemonset/log-agent -n ${NAMESPACE} --timeout=180s
echo "==> Applying CronJob"
kubectl apply -f k8s/cronjob.yaml
echo "==> Applying LogReadAll"
kubectl apply -f k8s/log-read-all.yaml
echo "==> Applying Istio Gateway"
kubectl apply -f k8s/istio-gateway.yaml
echo "==> Applying Istio VirtualService"
kubectl apply -f k8s/istio-virtualservice.yaml
echo "==> Applying Istio DestinationRules"
kubectl apply -f k8s/istio-destinationrule.yaml
echo "==> Resources in ${NAMESPACE}:"
kubectl get all -n ${NAMESPACE}
echo
echo "==> Istio resources in ${NAMESPACE}:"
kubectl get gateway,virtualservice,destinationrule -n ${NAMESPACE}
echo
echo "Done."
echo "To test:"
echo "kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80"

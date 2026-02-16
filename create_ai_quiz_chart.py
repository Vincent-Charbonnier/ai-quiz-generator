import os
import shutil

chart_name = "ai-quiz-generator"
chart_version = "0.1.0"
base_dir = f"./{chart_name}"
templates_dir = os.path.join(base_dir, "templates")

# Delete old chart if exists
if os.path.exists(base_dir):
    print(f"Removing existing chart at '{base_dir}'...")
    shutil.rmtree(base_dir)

# Create folder structure
print(f"Creating Helm chart directory structure at '{base_dir}'...")
os.makedirs(templates_dir, exist_ok=True)

# ---------------------------
# Chart.yaml
# ---------------------------
print("Writing Chart.yaml...")
chart_yaml = f"""\
apiVersion: v2
name: {chart_name}
description: Helm chart for vinchar/ai-quiz-generator (frontend + backend)
type: application
version: {chart_version}
appVersion: "{chart_version}"
"""
with open(os.path.join(base_dir, "Chart.yaml"), "w") as f:
    f.write(chart_yaml)

# ---------------------------
# values.yaml
# ---------------------------
print("Writing values.yaml...")
values_yaml = """\
replicaCount:
  frontend: 1
  backend: 1

image:
  frontend:
    repository: vinchar/ai-quiz-generator-frontend
    tag: "0.1"
    pullPolicy: IfNotPresent
  backend:
    repository: vinchar/ai-quiz-generator-backend
    tag: "0.1"
    pullPolicy: IfNotPresent

service:
  frontend:
    type: ClusterIP
    port: 80
  backend:
    # IMPORTANT: nginx in the frontend image proxies to http://backend:3001
    # Keep this name as "backend" unless you rebuild the frontend image.
    name: backend
    type: ClusterIP
    port: 3001

resources:
  frontend:
    limits: {}
    requests: {}
  backend:
    limits: {}
    requests: {}

nodeSelector: {}
tolerations: []
affinity: {}

readinessProbe:
  frontend:
    path: "/"
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  backend:
    path: "/api/generate"
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1

livenessProbe:
  frontend:
    path: "/"
    initialDelaySeconds: 30
    periodSeconds: 20
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  backend:
    path: "/api/generate"
    initialDelaySeconds: 30
    periodSeconds: 20
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1

hpa:
  enabled: false
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 60

ingress:
  enabled: false
  host: ai-quiz.example.com
  annotations: {}

ezua:
  virtualService:
    endpoint: "ai-quiz.${DOMAIN_NAME}"
    domain: "${DOMAIN_NAME}"
    istioGateway: "istio-system/ezaf-gateway"
"""
with open(os.path.join(base_dir, "values.yaml"), "w") as f:
    f.write(values_yaml)

# ---------------------------
# Frontend Deployment
# ---------------------------
print("Writing frontend-deployment.yaml...")
frontend_deployment_yaml = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-frontend
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  replicas: {{ .Values.replicaCount.frontend }}
  selector:
    matchLabels:
      app: {{ include "ai-quiz-generator.name" . }}
      app.kubernetes.io/component: frontend
  template:
    metadata:
      labels:
        app: {{ include "ai-quiz-generator.name" . }}
        app.kubernetes.io/component: frontend
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: frontend
          image: "{{ .Values.image.frontend.repository }}:{{ .Values.image.frontend.tag }}"
          imagePullPolicy: {{ .Values.image.frontend.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.frontend.port }}
          readinessProbe:
            httpGet:
              path: {{ .Values.readinessProbe.frontend.path | quote }}
              port: {{ .Values.service.frontend.port }}
            initialDelaySeconds: {{ .Values.readinessProbe.frontend.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.frontend.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.frontend.timeoutSeconds }}
            failureThreshold: {{ .Values.readinessProbe.frontend.failureThreshold }}
            successThreshold: {{ .Values.readinessProbe.frontend.successThreshold }}
          livenessProbe:
            httpGet:
              path: {{ .Values.livenessProbe.frontend.path | quote }}
              port: {{ .Values.service.frontend.port }}
            initialDelaySeconds: {{ .Values.livenessProbe.frontend.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.frontend.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.frontend.timeoutSeconds }}
            failureThreshold: {{ .Values.livenessProbe.frontend.failureThreshold }}
            successThreshold: {{ .Values.livenessProbe.frontend.successThreshold }}
          resources:
            {{- toYaml .Values.resources.frontend | nindent 12 }}
"""
with open(os.path.join(templates_dir, "frontend-deployment.yaml"), "w") as f:
    f.write(frontend_deployment_yaml)

# ---------------------------
# Backend Deployment
# ---------------------------
print("Writing backend-deployment.yaml...")
backend_deployment_yaml = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-backend
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: {{ .Values.replicaCount.backend }}
  selector:
    matchLabels:
      app: {{ include "ai-quiz-generator.name" . }}
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        app: {{ include "ai-quiz-generator.name" . }}
        app.kubernetes.io/component: backend
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: backend
          image: "{{ .Values.image.backend.repository }}:{{ .Values.image.backend.tag }}"
          imagePullPolicy: {{ .Values.image.backend.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.backend.port }}
          readinessProbe:
            httpGet:
              path: {{ .Values.readinessProbe.backend.path | quote }}
              port: {{ .Values.service.backend.port }}
            initialDelaySeconds: {{ .Values.readinessProbe.backend.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.backend.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.backend.timeoutSeconds }}
            failureThreshold: {{ .Values.readinessProbe.backend.failureThreshold }}
            successThreshold: {{ .Values.readinessProbe.backend.successThreshold }}
          livenessProbe:
            httpGet:
              path: {{ .Values.livenessProbe.backend.path | quote }}
              port: {{ .Values.service.backend.port }}
            initialDelaySeconds: {{ .Values.livenessProbe.backend.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.backend.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.backend.timeoutSeconds }}
            failureThreshold: {{ .Values.livenessProbe.backend.failureThreshold }}
            successThreshold: {{ .Values.livenessProbe.backend.successThreshold }}
          resources:
            {{- toYaml .Values.resources.backend | nindent 12 }}
"""
with open(os.path.join(templates_dir, "backend-deployment.yaml"), "w") as f:
    f.write(backend_deployment_yaml)

# ---------------------------
# Frontend Service
# ---------------------------
print("Writing frontend-service.yaml...")
frontend_service_yaml = """\
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-frontend
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  type: {{ .Values.service.frontend.type }}
  ports:
    - port: {{ .Values.service.frontend.port }}
      targetPort: {{ .Values.service.frontend.port }}
      protocol: TCP
      name: http
  selector:
    app: {{ include "ai-quiz-generator.name" . }}
    app.kubernetes.io/component: frontend
"""
with open(os.path.join(templates_dir, "frontend-service.yaml"), "w") as f:
    f.write(frontend_service_yaml)

# ---------------------------
# Backend Service
# ---------------------------
print("Writing backend-service.yaml...")
backend_service_yaml = """\
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.service.backend.name }}
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  type: {{ .Values.service.backend.type }}
  ports:
    - port: {{ .Values.service.backend.port }}
      targetPort: {{ .Values.service.backend.port }}
      protocol: TCP
      name: http
  selector:
    app: {{ include "ai-quiz-generator.name" . }}
    app.kubernetes.io/component: backend
"""
with open(os.path.join(templates_dir, "backend-service.yaml"), "w") as f:
    f.write(backend_service_yaml)

# ---------------------------
# HorizontalPodAutoscaler (optional)
# ---------------------------
print("Writing hpa.yaml...")
hpa_yaml = """\
{{- if .Values.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "ai-quiz-generator.fullname" . }}-frontend
  minReplicas: {{ .Values.hpa.minReplicas }}
  maxReplicas: {{ .Values.hpa.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.hpa.targetCPUUtilizationPercentage }}
{{- end }}
"""
with open(os.path.join(templates_dir, "hpa.yaml"), "w") as f:
    f.write(hpa_yaml)

# ---------------------------
# VirtualService (Istio) for Frontend
# ---------------------------
print("Writing virtualservice.yaml...")
virtualservice_yaml = """\
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-frontend
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  gateways:
    - {{ .Values.ezua.virtualService.istioGateway }}
  hosts:
    - {{ .Values.ezua.virtualService.endpoint }}
  http:
    - match:
        - uri:
            prefix: /
      rewrite:
        uri: /
      route:
        - destination:
            host: {{ include "ai-quiz-generator.fullname" . }}-frontend.{{ .Release.Namespace }}.svc.cluster.local
            port:
              number: {{ .Values.service.frontend.port }}
"""
with open(os.path.join(templates_dir, "virtualservice.yaml"), "w") as f:
    f.write(virtualservice_yaml)

# ---------------------------
# NOTES.txt
# ---------------------------
print("Writing NOTES.txt...")
notes_txt = """\
Thank you for installing the ai-quiz-generator chart!

This chart deploys two components:
  - frontend (nginx) on port 80
  - backend (Express) on port 3001

IMPORTANT:
The frontend image proxies API requests to http://backend:3001.
Keep the backend service name as "backend" (values.yaml) unless you rebuild the frontend image.

Install the chart:
  helm install ai-quiz-generator ./ai-quiz-generator

To upgrade with new values:
  helm upgrade --install ai-quiz-generator ./ai-quiz-generator -f my-values.yaml

If using Istio, ensure your gateway in values (ezua.virtualService.istioGateway) is correct.

For local testing via port-forward:
  kubectl port-forward svc/$(kubectl get svc -l app.kubernetes.io/name=ai-quiz-generator -o jsonpath='{.items[0].metadata.name}') 8080:80

"""
with open(os.path.join(templates_dir, "NOTES.txt"), "w") as f:
    f.write(notes_txt)

# ---------------------------
# Helpers (names, labels)
# ---------------------------
print("Writing _helpers.tpl...")
helpers_tpl = """\
{{/*
Chart name (ai-quiz-generator)
*/}}
{{- define "ai-quiz-generator.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Full name (release-ai-quiz-generator)
*/}}
{{- define "ai-quiz-generator.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "ai-quiz-generator.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Standard labels
*/}}
{{- define "ai-quiz-generator.labels" -}}
app.kubernetes.io/name: {{ include "ai-quiz-generator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
"""
with open(os.path.join(templates_dir, "_helpers.tpl"), "w") as f:
    f.write(helpers_tpl)

print(f"Helm chart folder created at: {base_dir}")

# ---------------------------
# Package the chart
# ---------------------------
print("Packaging Helm chart into .tgz archive...")
exit_code = os.system(f"helm package {base_dir}")

if exit_code == 0:
    print("Chart packaged successfully!")
    print("Install with:")
    print(f"  helm install ai-quiz-generator {chart_name}-{chart_version}.tgz")
else:
    print("Failed to package chart. Ensure Helm is installed and on PATH.")

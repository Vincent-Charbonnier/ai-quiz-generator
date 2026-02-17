import os
import shutil

chart_name = "ai-quiz-generator"
chart_version = "0.1.9"
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
description: Helm chart for vinchar/ai-quiz-generator (frontend + backend + rag)
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
  rag: 1

image:
  frontend:
    repository: vinchar/ai-quiz-generator-frontend
    tag: "0.5"
    pullPolicy: IfNotPresent
  backend:
    repository: vinchar/ai-quiz-generator-backend
    tag: "0.3"
    pullPolicy: IfNotPresent
  rag:
    repository: vinchar/ai-quiz-generator-rag
    tag: "0.3"
    pullPolicy: IfNotPresent

frontend:
  nginx:
    enabled: true
    config: |
      server {
          listen 80;
          root /usr/share/nginx/html;
          index index.html;

          client_max_body_size 50m;

          location /api/ {
              proxy_pass http://backend:3001;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_read_timeout 300s;
              proxy_send_timeout 300s;
              proxy_connect_timeout 60s;
          }

          location /health {
              proxy_pass http://backend:3001/health;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
          }

          location / {
              try_files $uri $uri/ /index.html;
          }
      }

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
  rag:
    name: rag
    type: ClusterIP
    port: 8000

ragConfig:
  pdfUrl: ""
  embeddingEndpoint: "https://nv-embedqa-e5-v5.vincent-charbon-8e171347.serving.pcaidev.ai.greendatacenter.com/v1"
  embeddingToken: ""
  embeddingModel: "nvidia/nv-embedqa-e5-v5"
  llmEndpoint: "https://gpt-oss-120b.project-user-claudio-luethi.serving.pcaidev.ai.greendatacenter.com/v1"
  llmToken: ""
  llmModel: "openai/gpt-oss-120b"
  chunkSize: 512
  chunkOverlap: 64
  topK: 6
  chromaUrl: "http://chroma-db-service.chroma.svc.cluster.local:8000"
  chromaSslVerify: "true"

configMap:
  create: true
  name: ""

secret:
  create: true
  name: ""

resources:
  frontend:
    limits: {}
    requests: {}
  backend:
    limits: {}
    requests: {}
  rag:
    limits:
      cpu: "2"
      memory: "16Gi"
    requests:
      cpu: "1"
      memory: "8Gi"

backend:
  configPath: "/data/quiz-config.json"
  persistence:
    enabled: true
    accessModes:
      - ReadWriteOnce
    size: 1Gi
    storageClassName: ""
    mountPath: "/data"

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
    path: "/health"
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  rag:
    path: "/healthz"
    initialDelaySeconds: 20
    periodSeconds: 15
    timeoutSeconds: 10
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
    path: "/health"
    initialDelaySeconds: 30
    periodSeconds: 20
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  rag:
    path: "/healthz"
    initialDelaySeconds: 60
    periodSeconds: 30
    timeoutSeconds: 10
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
    timeout: "300s"
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
          {{- if .Values.frontend.nginx.enabled }}
          volumeMounts:
            - name: nginx-conf
              mountPath: /etc/nginx/conf.d/default.conf
              subPath: default.conf
          {{- end }}
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
      {{- if .Values.frontend.nginx.enabled }}
      volumes:
        - name: nginx-conf
          configMap:
            name: {{ include "ai-quiz-generator.fullname" . }}-nginx
      {{- end }}
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
          env:
            - name: RAG_URL
              value: "http://{{ .Values.service.rag.name }}:{{ .Values.service.rag.port }}/chat/completions"
            - name: CONFIG_PATH
              value: {{ .Values.backend.configPath | quote }}
          envFrom:
            - configMapRef:
                name: {{ include "ai-quiz-generator.configMapName" . }}
            - secretRef:
                name: {{ include "ai-quiz-generator.secretName" . }}
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
          {{- if .Values.backend.persistence.enabled }}
          volumeMounts:
            - name: backend-config
              mountPath: {{ .Values.backend.persistence.mountPath | quote }}
          {{- end }}
      {{- if .Values.backend.persistence.enabled }}
      volumes:
        - name: backend-config
          persistentVolumeClaim:
            claimName: {{ include "ai-quiz-generator.fullname" . }}-backend-config
      {{- end }}
"""
with open(os.path.join(templates_dir, "backend-deployment.yaml"), "w") as f:
    f.write(backend_deployment_yaml)

# ---------------------------
# RAG Deployment
# ---------------------------
print("Writing rag-deployment.yaml...")
rag_deployment_yaml = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-rag
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: rag
spec:
  replicas: {{ .Values.replicaCount.rag }}
  selector:
    matchLabels:
      app: {{ include "ai-quiz-generator.name" . }}
      app.kubernetes.io/component: rag
  template:
    metadata:
      labels:
        app: {{ include "ai-quiz-generator.name" . }}
        app.kubernetes.io/component: rag
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
        - name: rag
          image: "{{ .Values.image.rag.repository }}:{{ .Values.image.rag.tag }}"
          imagePullPolicy: {{ .Values.image.rag.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.rag.port }}
          envFrom:
            - configMapRef:
                name: {{ include "ai-quiz-generator.configMapName" . }}
            - secretRef:
                name: {{ include "ai-quiz-generator.secretName" . }}
          readinessProbe:
            httpGet:
              path: {{ .Values.readinessProbe.rag.path | quote }}
              port: {{ .Values.service.rag.port }}
            initialDelaySeconds: {{ .Values.readinessProbe.rag.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.rag.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.rag.timeoutSeconds }}
            failureThreshold: {{ .Values.readinessProbe.rag.failureThreshold }}
            successThreshold: {{ .Values.readinessProbe.rag.successThreshold }}
          livenessProbe:
            httpGet:
              path: {{ .Values.livenessProbe.rag.path | quote }}
              port: {{ .Values.service.rag.port }}
            initialDelaySeconds: {{ .Values.livenessProbe.rag.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.rag.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.rag.timeoutSeconds }}
            failureThreshold: {{ .Values.livenessProbe.rag.failureThreshold }}
            successThreshold: {{ .Values.livenessProbe.rag.successThreshold }}
          resources:
            {{- toYaml .Values.resources.rag | nindent 12 }}
"""
with open(os.path.join(templates_dir, "rag-deployment.yaml"), "w") as f:
    f.write(rag_deployment_yaml)

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
# RAG Service
# ---------------------------
print("Writing rag-service.yaml...")
rag_service_yaml = """\
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.service.rag.name }}
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: rag
spec:
  type: {{ .Values.service.rag.type }}
  ports:
    - port: {{ .Values.service.rag.port }}
      targetPort: {{ .Values.service.rag.port }}
      protocol: TCP
      name: http
  selector:
    app: {{ include "ai-quiz-generator.name" . }}
    app.kubernetes.io/component: rag
"""
with open(os.path.join(templates_dir, "rag-service.yaml"), "w") as f:
    f.write(rag_service_yaml)

# ---------------------------
# ConfigMap / Secret
# ---------------------------
print("Writing configmap.yaml...")
configmap_yaml = """\
{{- if .Values.configMap.create }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ai-quiz-generator.configMapName" . }}
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
data:
  RAG_PDF_URL: {{ .Values.ragConfig.pdfUrl | quote }}
  RAG_EMBEDDING_ENDPOINT: {{ .Values.ragConfig.embeddingEndpoint | quote }}
  RAG_EMBEDDING_MODEL: {{ .Values.ragConfig.embeddingModel | quote }}
  RAG_LLM_ENDPOINT: {{ .Values.ragConfig.llmEndpoint | quote }}
  RAG_LLM_MODEL: {{ .Values.ragConfig.llmModel | quote }}
  RAG_CHUNK_SIZE: {{ .Values.ragConfig.chunkSize | quote }}
  RAG_CHUNK_OVERLAP: {{ .Values.ragConfig.chunkOverlap | quote }}
  RAG_TOP_K: {{ .Values.ragConfig.topK | quote }}
  RAG_CHROMA_URL: {{ .Values.ragConfig.chromaUrl | quote }}
  RAG_CHROMA_SSL_VERIFY: {{ .Values.ragConfig.chromaSslVerify | quote }}
{{- end }}
"""
with open(os.path.join(templates_dir, "configmap.yaml"), "w") as f:
    f.write(configmap_yaml)

print("Writing secret.yaml...")
secret_yaml = """\
{{- if .Values.secret.create }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "ai-quiz-generator.secretName" . }}
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
type: Opaque
stringData:
  RAG_EMBEDDING_TOKEN: {{ .Values.ragConfig.embeddingToken | quote }}
  RAG_LLM_TOKEN: {{ .Values.ragConfig.llmToken | quote }}
{{- end }}
"""
with open(os.path.join(templates_dir, "secret.yaml"), "w") as f:
    f.write(secret_yaml)

# ---------------------------
# Frontend Nginx ConfigMap
# ---------------------------
print("Writing frontend-nginx-configmap.yaml...")
frontend_nginx_configmap_yaml = """\
{{- if .Values.frontend.nginx.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-nginx
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
data:
  default.conf: |
{{ .Values.frontend.nginx.config | nindent 4 }}
{{- end }}
"""
with open(os.path.join(templates_dir, "frontend-nginx-configmap.yaml"), "w") as f:
    f.write(frontend_nginx_configmap_yaml)

# ---------------------------
# Backend PVC
# ---------------------------
print("Writing backend-pvc.yaml...")
backend_pvc_yaml = """\
{{- if .Values.backend.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "ai-quiz-generator.fullname" . }}-backend-config
  labels:
    {{- include "ai-quiz-generator.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  accessModes:
{{- range .Values.backend.persistence.accessModes }}
    - {{ . | quote }}
{{- end }}
  resources:
    requests:
      storage: {{ .Values.backend.persistence.size | quote }}
  {{- if .Values.backend.persistence.storageClassName }}
  storageClassName: {{ .Values.backend.persistence.storageClassName | quote }}
  {{- end }}
{{- end }}
"""
with open(os.path.join(templates_dir, "backend-pvc.yaml"), "w") as f:
    f.write(backend_pvc_yaml)

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
      timeout: {{ .Values.ezua.virtualService.timeout | quote }}
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

This chart deploys three components:
  - frontend (nginx) on port 80
  - backend (Express) on port 3001
  - rag (FastAPI) on port 8000

IMPORTANT:
The frontend image proxies API requests to http://backend:3001.
Keep the backend service name as "backend" (values.yaml) unless you rebuild the frontend image.
The backend calls the RAG service at http://rag:8000/chat/completions.
Keep the rag service name as "rag" unless you change RAG_URL.

PDF SOURCE:
- For runtime uploads, users upload PDFs in the UI (recommended).
- For fixed documents, set ragConfig.pdfUrl in values to a hosted PDF.
CHROMA:
- To use an external Chroma server, set ragConfig.chromaUrl (e.g. http://chroma-db.svc.cluster.local:8000).
- Set ragConfig.chromaSslVerify to "false" if the server uses an untrusted certificate.

CONFIG:
- By default, a ConfigMap and Secret are created from values.yaml and mounted as env vars in backend and rag.
- For existing resources, set configMap.name / secret.name and set create=false.
- The backend can persist the last-used config to a PVC. See backend.persistence in values.yaml.

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

{{/*
ConfigMap name
*/}}
{{- define "ai-quiz-generator.configMapName" -}}
{{- if .Values.configMap.name -}}
{{- .Values.configMap.name -}}
{{- else -}}
{{ include "ai-quiz-generator.fullname" . }}-config
{{- end -}}
{{- end }}

{{/*
Secret name
*/}}
{{- define "ai-quiz-generator.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{ include "ai-quiz-generator.fullname" . }}-secret
{{- end -}}
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

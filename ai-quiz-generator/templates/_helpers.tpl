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

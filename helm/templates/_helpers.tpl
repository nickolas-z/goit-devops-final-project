{{/* Назва чарта */}}
{{- define "aiops-quality.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Повна назва релізу */}}
{{- define "aiops-quality.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/* Chart label */}}
{{- define "aiops-quality.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Спільні labels */}}
{{- define "aiops-quality.labels" -}}
helm.sh/chart: {{ include "aiops-quality.chart" . }}
{{ include "aiops-quality.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Selector labels */}}
{{- define "aiops-quality.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aiops-quality.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* ServiceAccount name */}}
{{- define "aiops-quality.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "aiops-quality.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/* Тег образу: image.tag або appVersion */}}
{{- define "aiops-quality.imageTag" -}}
{{- default .Chart.AppVersion .Values.image.tag -}}
{{- end -}}

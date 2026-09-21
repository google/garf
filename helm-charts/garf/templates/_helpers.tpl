{{/*
Expand the name of the chart.
*/}}
{{- define "garf.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 56 | trimSuffix "-" }}
{{- end }}

{{/*
Worker name.
*/}}
{{- define "garf.workerName" -}}
{{ printf "%s-worker" (include "garf.fullname" .) }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 56 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "garf.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 56 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 56 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 56 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "garf.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 56 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "garf.labels" -}}
helm.sh/chart: {{ include "garf.chart" . }}
{{ include "garf.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "garf.selectorLabels" -}}
app.kubernetes.io/name: {{ include "garf.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common worker labels
*/}}
{{- define "garf.workerLabels" -}}
helm.sh/chart: {{ include "garf.chart" . }}
{{ include "garf.workerSelectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "garf.workerSelectorLabels" -}}
app.kubernetes.io/name: {{ include "garf.workerName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{/*
Create the name of the service account to use
*/}}
{{- define "garf.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "garf.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create redis connection string
*/}}
{{- define "garf.redisUrl" -}}
{{- $fullname := include "garf.fullname" . -}}
{{- printf "redis://:%s@%s-redis-master:%v/0" .Values.redis.auth.password $fullname .Values.redis.master.containerPorts.redis }}
{{- end }}


{{/*
Render env variables
*/}}
{{- define "garf.renderEnv" -}}
{{- range $key, $val := . }}
- name: {{ $key }}
  {{- if kindIs "map" $val }}
{{ toYaml $val | indent 2 }}
  {{- else }}
  value: {{ $val | quote }}
  {{- end }}
{{- end }}
{{- end -}}

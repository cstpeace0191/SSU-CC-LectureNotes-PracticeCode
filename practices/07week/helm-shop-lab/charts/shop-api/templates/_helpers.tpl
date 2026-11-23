{{/* 차트 이름 */}}
{{- define "shop-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* 리소스 전체 이름: <릴리스>-<차트> (릴리스 이름에 차트 이름이 이미 있으면 그대로) */}}
{{- define "shop-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/* 셀렉터 라벨 — 배포 후 바뀌면 안 되는 최소 집합 */}}
{{- define "shop-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "shop-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* 공통 라벨 */}}
{{- define "shop-api.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{ include "shop-api.selectorLabels" . }}
app.kubernetes.io/version: {{ include "shop-api.imageTag" . | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: helm-shop-lab
{{- end }}

{{/* 이미지 태그: values 의 tag 우선, 없으면 appVersion */}}
{{- define "shop-api.imageTag" -}}
{{- default .Chart.AppVersion .Values.image.tag }}
{{- end }}

{{- define "shop-api.image" -}}
{{- printf "%s:%s" .Values.image.repository (include "shop-api.imageTag" .) }}
{{- end }}

{{/* DB 접속 환경변수 — Deployment 와 마이그레이션 Job 이 함께 사용 */}}
{{- define "shop-api.databaseEnv" -}}
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ required "database.existingSecret 값이 필요합니다" .Values.database.existingSecret }}
      key: {{ .Values.database.passwordKey }}
- name: DATABASE_URL
  value: {{ printf "postgresql://%s:$(DB_PASSWORD)@%s:%v/%s" .Values.database.user .Values.database.host .Values.database.port .Values.database.name | quote }}
{{- end }}

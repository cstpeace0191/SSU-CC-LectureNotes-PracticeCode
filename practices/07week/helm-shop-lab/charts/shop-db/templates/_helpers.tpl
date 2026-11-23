{{- define "shop-db.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: shop-db
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: helm-shop-lab
{{- end }}

{{- define "shop-db.selectorLabels" -}}
app.kubernetes.io/name: shop-db
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

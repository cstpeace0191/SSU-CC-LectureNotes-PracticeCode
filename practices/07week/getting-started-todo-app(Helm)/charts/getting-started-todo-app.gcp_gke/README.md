# getting-started-todo-app

A Helm chart for getting-started-todo-app

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
# Standard Helm install
$ helm install  my-release getting-started-todo-app

# To use a custom namespace and force the creation of the namespace
$ helm install my-release --namespace my-namespace --create-namespace getting-started-todo-app

# To use a custom values file
$ helm install my-release -f my-values.yaml getting-started-todo-app
```

See the [Helm documentation](https://helm.sh/docs/intro/using_helm/) for more information on installing and managing the chart.

## Configuration

The following table lists the configurable parameters of the getting-started-todo-app chart and their default values.

| Parameter                                               | Default                                                                       |
| ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `backend.imagePullPolicy`                               | `IfNotPresent`                                                                |
| `backend.replicas`                                      | `1`                                                                           |
| `backend.repository.image`                              | `asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend` |
| `backend.repository.tag`                                | `prod`                                                                        |
| `backend.serviceAccount`                                | ``                                                                            |
| `mysql.imagePullPolicy`                                 | `IfNotPresent`                                                                |
| `mysql.persistence.todo_mysql_data.accessMode[0].value` | `ReadWriteOnce`                                                               |
| `mysql.persistence.todo_mysql_data.enabled`             | `true`                                                                        |
| `mysql.persistence.todo_mysql_data.size`                | `1Gi`                                                                         |
| `mysql.persistence.todo_mysql_data.storageClass`        | `-`                                                                           |
| `mysql.replicas`                                        | `1`                                                                           |
| `mysql.repository.image`                                | `mysql`                                                                       |
| `mysql.repository.tag`                                  | `9.3`                                                                         |
| `mysql.serviceAccount`                                  | ``                                                                            |



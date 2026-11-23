<div style="text-align:center; margin: auto 0 4em 0" align="center">
<img src="https://repo.katenary.io/Katenary/katenary/raw/branch/master/doc/docs/statics/logo-vertical.svg" alt="Katenary Logo" style="max-width: 90%" align="center"/>
</div>

<div style="text-align:center; margin: auto 0 4em 0" align="center">

[![Documentation Status](https://readthedocs.org/projects/katenary/badge/?version=latest)](https://katenary.readthedocs.io/latest/?badge=latest)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=katenary_katenary&metric=coverage)](https://sonarcloud.io/summary/new_code?id=katenary_katenary)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=katenary_katenary&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=katenary_katenary)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=katenary_katenary&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=katenary_katenary)

</div>

<div style="text-align:center; margin: auto 0 4em 0" align="center">
<h3>🚀 Unleash Productivity with Katenary! 🚀</h3>
</div>

Tired of manual conversions? Katenary harnesses the labels from your "`compose`" file to craft complete Helm Charts
effortlessly, saving you time and energy.

🛠️ Simple automated CLI: Katenary handles the grunt work, generating everything needed for seamless service binding
and Helm Chart creation.

💡 Effortless Efficiency: You only need to add labels when it's necessary to precise things.
Then call `katenary convert` and let the magic happen.

---

## What is Katenary?

Katenary is a tool to transform `compose` (`docker compose`, `podman compose`, `nerdctl compose`, ...) files
into a working Helm Chart for Kubernetes.

Today, it is partially developed in collaboration with [Klee Group](https://www.kleegroup.com). Note that Katenary is
and **will stay an open source and free (as freedom) project**. We are convinced that the best way to make it better is to
share it with the community.

The main developer is [Patrice FERLET](https://repo.katenary.io/metal3d).

---

## 📌 Usage in this Project (`getting-started-todo-app`)

This project uses Katenary to convert environment-specific Docker Compose files into production-ready Kubernetes Helm Charts.

### Project Environment & Chart Mapping

| Environment | Source Compose File | Generated Helm Chart Path | Target Cluster & Container Image | Documentation Guide |
|---|---|---|---|---|
| **Local KIND (Local)** | `compose-local_kind.yaml` | `charts/getting-started-todo-app.local_kind` | Local KIND (`todo-backend:prod`) | [README-local_kind.md](charts/getting-started-todo-app.local_kind/README-local_kind.md) |
| **GitHub Packages (GHCR)** | `compose-github_kind.yaml` | `charts/getting-started-todo-app.github_kind` | KIND / Remote GHCR (`ghcr.io/...`) | [README-github_kind.md](charts/getting-started-todo-app.github_kind/README-github_kind.md) |
| **GCP Artifact Registry / GKE** | `compose-gcp_gke.yaml` | `charts/getting-started-todo-app.gcp_gke` | GKE / GCP Artifact Registry (`asia-northeast3-docker.pkg.dev/...`) | [README-gcp_gke.md](charts/getting-started-todo-app.gcp_gke/README-gcp_gke.md) |

### Katenary Conversion Commands in this Project

Execute the conversion command for the desired environment from the project root:

```bash
# 1. Local KIND Chart
katenary convert -c compose-local_kind.yaml -o charts/getting-started-todo-app.local_kind -a 1.0.0 -v 0.1.0 -f

# 2. GitHub Packages (GHCR) Chart
katenary convert -c compose-github_kind.yaml -o charts/getting-started-todo-app.github_kind -a 1.0.0 -v 0.1.0 -f

# 3. GCP Artifact Registry / GKE Chart
katenary convert -c compose-gcp_gke.yaml -o charts/getting-started-todo-app.gcp_gke -a 1.0.0 -v 0.1.0 -f
```

- **Command Options**:
  - `-c <file>`: Specifies the source Docker Compose file.
  - `-o <dir>`: Specifies the target Helm Chart output directory.
  - `-a 1.0.0`: Sets `appVersion` in `Chart.yaml` (application release version).
  - `-v 0.1.0`: Sets `version` in `Chart.yaml` (Helm chart version).
  - `-f`: Forces overwriting of the target directory without interactive prompt.

### Real Project Compose Example (`compose-local_kind.yaml`)

Below is the actual Compose configuration used in this repository showing how Katenary labels are applied:

```yaml
services:
  # 1) Local Traefik Proxy: Excluded from Kubernetes Chart
  proxy:
    image: traefik:v3.6
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - 80:80
      - 443:443
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    labels:
      katenary.v3/ignore: "true"   # Tells Katenary not to generate manifests for the proxy

  # 2) Backend Production Service: Express API + Bundled React Frontend
  backend:
    image: todo-backend:prod
    build:
      context: ./
      target: final                # Multi-stage build final stage with bundled static assets
    ports:
      - 3000:3000                  # Required for Katenary to generate a Kubernetes ClusterIP Service
    expose:
      - 3000
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: root
      MYSQL_PASSWORD: secret
      MYSQL_DB: todos    
    depends_on:
      mysql:
        condition: service_healthy # Katenary generates a wait-for-mysql InitContainer automatically
    labels:
      # Dynamic Kubernetes Service DNS binding:
      # Replaces MYSQL_HOST with Helm templated service name '{{ include "<chart>.fullname" . }}-mysql'
      katenary.v3/map-env: |-
        MYSQL_HOST: '{{ include "__APP__.fullname" . }}-mysql'

  # 3) MySQL Database Service
  mysql:
    image: mysql:9.3
    ports:
      - 3306:3306
    expose:
      - 3306
    volumes:
      - todo-mysql-data:/var/lib/mysql # Katenary generates a PersistentVolumeClaim (PVC)
    environment: 
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: todos
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### Generated Chart Directory Structure

For the Local KIND chart (`charts/getting-started-todo-app.local_kind/`), Katenary generates:

```text
charts/getting-started-todo-app.local_kind/
├── Chart.yaml              # Chart metadata (name: getting-started-todo-app, version: 0.1.0, appVersion: 1.0.0)
├── README-local_kind.md    # Deployment guide for local KIND cluster
├── values.yaml             # Configurable parameters (replicas, image, resources, persistence)
└── templates/              # Rendered Kubernetes manifests
    ├── _helpers.tpl        # Template helper definitions
    ├── backend/            # Deployment, Service, and ConfigMap for the backend service
    │   ├── configmap.yaml
    │   ├── deployment.yaml
    │   └── service.yaml
    └── mysql/              # Deployment, Service, PVC, and ConfigMap for MySQL
        ├── configmap.yaml
        ├── deployment.yaml
        ├── service.yaml
        └── todo_mysql_data.volumeclaim.yaml
```

---

## Installation

### In this Project Workspace (Windows)

The standalone binary `katenary.exe` is already included directly in this project's root folder!

You can run it directly using PowerShell:
```powershell
.\katenary.exe version
```

To add it to your current session `Path`:
```powershell
$env:Path += ";$pwd"
katenary version
```

### Package from Repository & Windows Installer

You can find Linux packages repository and Windows installer in the [packages page](https://repo.katenary.io/Katenary/katenary/packages).

> Note for Fedora >= 42, the repository instructions are not up-to-date. You should use:
>
> ```bash
> dnf config-manager addrepo \
>   --from-repofile https://repo.katenary.io/Katenary/katenary/fedora/katenary.repo
> dnf install katenary
> ```

- **Windows users**: Go to the "generic" packages page and download the `setup.exe` file.
- **macOS users**: Please use the "`darwin`" binary. An experimental package is in preparation.
- **FreeBSD users**: Please use the "`freebsd`" package in the "generic" packages page.

### Binary Installation

You can download the binaries from the [Releases](https://repo.katenary.io/Katenary/katenary/releases) section. Copy the binary, rename it to `katenary`, and place it inside your `PATH`.

On Linux, you can use the `install.sh` from the repository to install it in `$HOME/.local/bin`:

```bash
sh <(curl -sSL https://repo.katenary.io/Katenary/katenary/raw/branch/master/install.sh)
```

On any OS with Go installed:

```bash
go install -u katenary.io/cmd@latest
# or specify a release tag
go install -u katenary.io/cmd@v3.0.0
```

### Build from Source

If you have `podman` or `docker`:

```bash
make build
make install
```

It uses default PREFIX (`~/.local/`) to install the binary in `bin`. To customize the PREFIX:

```bash
sudo make install PREFIX=/usr/local
```

Or build with your local Go compiler:

```bash
make build GO=local
# Force OS / architecture
make build GO=local GOOS=linux GOARCH=arm64
```

---

## Shell Completion Tips

Adding completion to your shell profile (`.bashrc`, `.zshrc`, etc.) is strongly recommended:

```bash
# bash in ~/.bashrc
source <(katenary completion bash)
# If descriptions break completion:
source <(katenary completion bash --no-description)

# zsh in ~/.zshrc
source <(katenary completion zsh)

# fish in ~/.config/fish/config.fish
katenary completion fish | source
```

---

## General CLI Usage

```text
Katenary is a tool to convert compose files to Helm Charts.

Each [command] and subcommand has got an "help" and "--help" flag to show more information.

Usage:
  katenary [command]

Examples:
  katenary convert -c docker-compose.yml -o ./charts

Available Commands:
  completion        Generates completion scripts
  convert           Converts a docker-compose file to a Helm Chart
  hash-composefiles Print the hash of the composefiles
  help              Help about any command
  help-labels       Print the labels help for all or a specific label
  schema            Print the schema of the katenary file
  version           Print the version number of Katenary

Flags:
  -h, --help      help for katenary
  -v, --version   version for katenary

Use "katenary [command] --help" for more information about a command.
```

---

## Katenary Labels Reference

These labels can be inspected with `katenary help-labels` and added to services in your Compose file:

```text
To get more information about a label, use: katenary help-label <name_without_prefix>
e.g. katenary help-label dependencies

katenary.v3/configmap-files:   []string                        Inject files as ConfigMap.
katenary.v3/cronjob:           object                          Create a cronjob from the service.
katenary.v3/dependencies:      []object                        Add Helm dependencies to the service.
katenary.v3/description:       string                          Description of the service.
katenary.v3/env-from:          []string                        Add environment variables from another service.
katenary.v3/exchange-volumes:  []object                        Add exchange volumes (emptyDir) to share data between containers.
katenary.v3/health-check:      object                          Health check to be added to the deployment.
katenary.v3/ignore:            bool                            Ignore the service (do not generate manifests).
katenary.v3/ingress:           object                          Ingress rules to be added to the service.
katenary.v3/main-app:          bool                            Mark the service as the main app.
katenary.v3/map-env:           map[string]string               Map env vars from the service to the deployment with template expressions.
katenary.v3/ports:             []uint32                        Ports to be added to the service.
katenary.v3/same-pod:          string                          Move the same-pod deployment to the target deployment.
katenary.v3/secrets:           []string                        Env vars to be set as Kubernetes Secrets.
katenary.v3/values:            []string or map[string]string   Environment variables to be added to values.yaml.
katenary.v3/values-from:       map[string]string               Add values from another service.
```

---

## Katenary.yaml File and Schema Validation

Instead of adding labels inside your Compose file, you can optionally define labels in a separate `katenary.yaml` file:

```yaml
web:
  ingress:
    hostname: myapp.example.com
    port: 80
```

To validate `katenary.yaml`, use the raw JSON schema:
`https://repo.katenary.io/Katenary/katenary/raw/branch/master/katenary.json`

### VSCode Configuration

Add the following to your VSCode `settings.json`:

```json
{
  "yaml.schemas": {
    "https://repo.katenary.io/Katenary/katenary/raw/branch/master/katenary.json": "katenary.yaml"
  }
}
```

### LazyVim / Neovim Configuration (`nvim-lspconfig`)

```lua
-- yaml.lua
return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        yamlls = {
          settings = {
            yaml = {
              schemas = {
                ["https://repo.katenary.io/Katenary/katenary/raw/branch/master/katenary.json"] = "katenary.yaml",
              },
            },
          },
        },
      },
    },
  },
}
```

---

## What a name…

Katenary is the stylized name of the project that comes from the "catenary" word.

A catenary is a curve formed by a wire, rope, or chain hanging freely from two points that are not in the same vertical line. For example, the anchor chain between a boat and the anchor.

This curved link represents what we try to do: the project is a stretched link from `docker-compose` to a `helm chart`.

---

## Related Project Links

- [Project Main README](README.md)
- [Helm Chart Deployment Guide](README(HelmChart).md)
- [Local KIND Deployment Guide](charts/getting-started-todo-app.local_kind/README-local_kind.md)
- [GitHub Packages (GHCR) Deployment Guide](charts/getting-started-todo-app.github_kind/README-github_kind.md)
- [GCP GKE Deployment Guide](charts/getting-started-todo-app.gcp_gke/README-gcp_gke.md)
- [Katenary Korean Documentation (한국어 설명서)](Katenary-README-KR.md)

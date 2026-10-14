# HashiCorp Vault Initial Secrets Generator

A lightweight utility to automate the creation and initialization of secrets in [HashiCorp Vault](https://www.vaultproject.io/) (KV v2 engine) from a declarative JSON configuration.

Designed primarily for bootstrapping infrastructure and CI/CD / Terraform pipelines, it safely creates initial credentials and configuration keys only if they do not already exist, avoiding unintended overwrites.

## Features

- **AppRole Authentication**: Authenticates to HashiCorp Vault via AppRole (`role_id` and `secret_id`).
- **Declarative Secret Provisioning**: Configure multiple Vault secret paths and key-value properties using a single JSON payload.
- **Dynamic & Static Properties**:
  - **Static**: Predefined constant values (e.g., usernames, hostnames, ports).
  - **Dynamic**: Automatically generates cryptographically random alphanumeric strings of configurable length, with optional prefixes and separators (e.g., passwords, API keys, tokens).
- **Idempotent & Safe**:
  - Reuses existing secret values fetched from Vault so passwords are not continuously rotated on every run.
  - Automatically provisions missing keys or updates secrets if required properties are missing.
- **Format Verification**: Validates whether existing dynamic secrets match expected length and prefix formats, with configurable recreation if a mismatch is detected.
- **Structured JSON Logging**: All logs are emitted in JSON format for easy ingestion by log aggregators (Elasticsearch/Loki/Datadog/CloudWatch).
- **Container Ready**: Built on top of Python 3.12 and [uv](https://docs.astral.sh/uv/) with an optimized Dockerfile.

## How It Works

1. **Authentication**: Authenticates with Vault using the configured AppRole credentials to obtain a client token.
2. **Secret Path Resolution**: For each secret in `SECRETS_TO_CREATE`, resolves the KV v2 path:
   - With `service_hostname`:
     `{kv_name}/data/{key_name_prefix}/{service_hostname}/{key_name}`
   - Without `service_hostname`:
     `{kv_name}/data/{key_name_prefix}/{key_name}`
3. **Inspection & Idempotency**:
   - Queries Vault for the secret at the resolved path.
   - If the secret **does not exist**, dynamic values are generated and the secret is created.
   - If the secret **exists**:
     - Compares configured properties against existing properties.
     - Preserves existing values for valid dynamic properties to avoid regenerating existing credentials.
     - Compares static values against expected values.
     - If all properties match, no action is taken.
     - If keys are missing or mismatched (or dynamic formatting failed with `RECREATE_IF_DYNAMIC_VALUE_MISMATCH=true`), the secret is updated.

## Environment Variables

Environment variable names with `TF_VAR_` prefixes allow direct compatibility with Terraform execution environments.

| Variable                             | Required | Default                 | Description                                                                                       |
| ------------------------------------ | :------: | ----------------------- | ------------------------------------------------------------------------------------------------- |
| `TF_VAR_VAULT_ADDRESS`               |    No    | `http://localhost:8200` | Vault server URL.                                                                                 |
| `TF_VAR_VAULT_APP_ROLE_LOGIN_PATH`   |    No    | `auth/approle/login`    | AppRole auth engine mount/login endpoint.                                                         |
| `TF_VAR_VAULT_APP_ROLE`              | **Yes**  | _None_                  | Vault AppRole Role ID.                                                                            |
| `TF_VAR_VAULT_APP_ROLE_SECRET_ID`    | **Yes**  | _None_                  | Vault AppRole Secret ID.                                                                          |
| `TF_VAR_VAULT_KV_NAME`               | **Yes**  | _None_                  | Vault KV v2 mount path (e.g., `secret`, `kv`).                                                    |
| `TF_VAR_VAULT_KV_PREFIX`             |    No    | _None_                  | Global KV prefix (optional / context dependent).                                                  |
| `SERVICE_HOSTNAME`                   |    No    | `""`                    | Optional hostname/service identifier inserted into secret paths.                                  |
| `SECRETS_TO_CREATE`                  | **Yes**  | `""`                    | JSON string defining the secrets and properties to provision.                                     |
| `RECREATE_IF_DYNAMIC_VALUE_MISMATCH` |    No    | `false`                 | If `true`, recreates dynamic secrets when existing values don't match the expected prefix/length. |
| `LOG_LEVEL`                          |    No    | `INFO`                  | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).                                              |

## Secrets Configuration Schema (`SECRETS_TO_CREATE`)

`SECRETS_TO_CREATE` must be a valid JSON array of secret configuration objects.

### Secret Object

| Field              |   Type   | Required | Default             | Description                                                          |
| ------------------ | :------: | :------: | ------------------- | -------------------------------------------------------------------- |
| `key_name_prefix`  | `string` | **Yes**  | -                   | Path prefix under the KV mount (e.g., `applications` or `database`). |
| `key_name`         | `string` | **Yes**  | -                   | Name of the secret key (e.g., `redis-credentials`).                  |
| `service_hostname` | `string` |    No    | Environment default | Overrides `SERVICE_HOSTNAME` for this specific secret path.          |
| `properties`       |  `list`  | **Yes**  | `[]`                | List of secret property objects stored under this secret key.        |

### Property Object

| Field                     |   Type   |     Required     | Default | Description                                                                |
| ------------------------- | :------: | :--------------: | ------- | -------------------------------------------------------------------------- |
| `name`                    | `string` |     **Yes**      | -       | Property key name inside the secret payload (e.g. `PASSWORD`, `API_KEY`).  |
| `value`                   | `string` |        No        | `""`    | Static value. If omitted or empty, the property is treated as **dynamic**. |
| `value_prefix`            | `string` |        No        | `""`    | Prefix prepended to generated dynamic values (e.g. `pg_`).                 |
| `value_length`            |  `int`   | No (for dynamic) | `0`     | Number of random alphanumeric characters generated for dynamic values.     |
| `value_section_separator` | `string` |        No        | `"-"`   | Separator between `value_prefix` and the random string.                    |

### Example JSON

```json
[
  {
    "key_name_prefix": "services",
    "key_name": "database",
    "properties": [
      {
        "name": "DB_HOST",
        "value": "postgres.internal.net"
      },
      {
        "name": "DB_PORT",
        "value": "5432"
      },
      {
        "name": "DB_USER",
        "value": "app_user"
      },
      {
        "name": "DB_PASSWORD",
        "value_prefix": "dbpass",
        "value_length": 32,
        "value_section_separator": "-"
      }
    ]
  },
  {
    "key_name_prefix": "infra",
    "key_name": "api-tokens",
    "service_hostname": "auth-service",
    "properties": [
      {
        "name": "SIGNING_KEY",
        "value_length": 64
      }
    ]
  }
]
```

With `TF_VAR_VAULT_KV_NAME="secret"`:

- The first secret path will be: `secret/data/services/database`
- The second secret path will be: `secret/data/infra/auth-service/api-tokens`

## Usage

### Local Execution with `uv`

Prerequisites: [uv](https://docs.astral.sh/uv/) and Python 3.12+.

1. Clone repository and install dependencies:

   ```bash
   git clone https://github.com/stanislawhorna/vault-initial-secrets-generator.git
   cd vault-initial-secrets-generator
   uv sync
   ```

2. Export environment variables and run:

   ```bash
   export TF_VAR_VAULT_ADDRESS="http://127.0.0.1:8200"
   export TF_VAR_VAULT_APP_ROLE="<your-role-id>"
   export TF_VAR_VAULT_APP_ROLE_SECRET_ID="<your-secret-id>"
   export TF_VAR_VAULT_KV_NAME="secret"
   export SECRETS_TO_CREATE='[{"key_name_prefix":"app","key_name":"creds","properties":[{"name":"API_KEY","value_length":32}]}]'

   uv run main.py
   ```

### Running with Docker

1. Build the Docker image:

   ```bash
   docker build -t vault-initial-secrets-generator .
   ```

2. Run the container:
   ```bash
   docker run --rm \
     -e TF_VAR_VAULT_ADDRESS="https://vault.example.com" \
     -e TF_VAR_VAULT_APP_ROLE="<role-id>" \
     -e TF_VAR_VAULT_APP_ROLE_SECRET_ID="<secret-id>" \
     -e TF_VAR_VAULT_KV_NAME="secret" \
     -e SECRETS_TO_CREATE='[...]' \
     vault-initial-secrets-generator
   ```

## Log Output Format

Logs are formatted as single-line JSON objects:

```json
{"level": "INFO", "timestamp": "2026-10-14 22:00:00,123", "message": "Application started"}
{"level": "INFO", "timestamp": "2026-10-14 22:00:00,250", "message": "Successfully authenticated with Vault at address 'http://localhost:8200'"}
{"level": "INFO", "timestamp": "2026-10-14 22:00:00,310", "message": "Key secret/data/app/creds does not exist in vault"}
{"level": "INFO", "timestamp": "2026-10-14 22:00:00,311", "message": "Generating new value for dynamic property 'API_KEY'"}
{"level": "INFO", "timestamp": "2026-10-14 22:00:00,420", "message": "Successfully created/updated key secret/data/app/creds. Current version: 1"}
```

## Project Structure

```text
vault-initial-secrets-generator/
├── Dockerfile                   # Multi-stage image packaging with uv
├── pyproject.toml               # Project metadata & dependencies
├── uv.lock                      # Locked dependency graph
├── main.py                      # Main entry point & reconciliation loop
└── src/
    ├── config.py                # Environment variable configuration
    ├── JsonLogFormatter.py      # Custom JSON logging formatter
    ├── SecretProperty.py        # Logic for static and dynamic property generation/comparison
    ├── VaultKeyConfiguration.py  # Deserialization and comparison of secret key configurations
    └── vault/
        ├── api_paths.py         # Vault API URL templates
        ├── KeyVault.py          # Vault response data structures
        └── VaultClient.py       # Vault HTTP client (authentication, read, write)
```

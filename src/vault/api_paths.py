

API_VERSION = "v1"
LOGIN_PATH = "{VAULT_ADDRESS}/{API_VERSION}/{AUTH_PATH}"

KV_PATH = "{VAULT_ADDRESS}/{API_VERSION}/{KV_PATH}"


KEY_PATH_PATTERN_NO_SERVICE_HOSTNAME = "{kv_name}/data/{kv_name_prefix}/{key_name}"
KEY_PATH_PATTERN = "{kv_name}/data/{kv_name_prefix}/{service_hostname}/{key_name}"


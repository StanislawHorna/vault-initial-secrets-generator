import logging
from dataclasses import dataclass, field
from src.vault.KeyVault import KeyVaultKey
from src.SecretProperty import SecretProperty
import src.vault.api_paths as api_paths
import src.config as config


@dataclass
class VaultKeyConfiguration:
    kv_name: str = field(init=False, default=config.VAULT_KV_NAME)
    key_name_prefix: str = field(init=True)
    key_name: str = field(init=True)

    service_hostname: str = field(init=True, default=config.SERVICE_HOSTNAME)

    properties: list[SecretProperty] = field(init=True, default_factory=list)
    path: str = field(init=False)

    def get_payload(self) -> dict[str, dict[str, str]]:
        return {"data": {p.name: p.value for p in self.properties}}

    def __post_init__(self):
        if self.service_hostname != "":
            self.path = api_paths.KEY_PATH_PATTERN.format(
                kv_name=self.kv_name,
                kv_name_prefix=self.key_name_prefix,
                service_hostname=self.service_hostname,
                key_name=self.key_name,
            )
        else:
            self.path = api_paths.KEY_PATH_PATTERN_NO_SERVICE_HOSTNAME.format(
                kv_name=self.kv_name,
                kv_name_prefix=self.key_name_prefix,
                key_name=self.key_name,
            )
        self.properties = [SecretProperty(**item) for item in self.properties]

    def __eq__(self, other) -> None:
        if not isinstance(other, KeyVaultKey):
            return NotImplemented

        if not (
            self.path == other.path and len(self.properties) == len(other.properties)
        ):
            logging.warning(
                f"Key path or number of properties mismatch (expected path: {self.path}, actual path: {other.path}, expected number of properties: {len(self.properties)}, actual number of properties: {len(other.properties)})"
            )
            return False

        properties_check = []
        for p in self.properties:
            matching = [v for _, v in other.properties.items() if v.name == p.name]
            if len(matching) != 1:
                logging.error(
                    f"Property '{p.name}' is missing in the vault key or there are multiple properties with the same name (expected 1, actual {len(matching)})"
                )
                properties_check.append(False)
                continue
            properties_check.append(p == matching[0])

        return all(properties_check)

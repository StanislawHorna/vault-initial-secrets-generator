import logging
import requests
from dataclasses import dataclass, field

import src.config as config
from .KeyVault import KeyVaultKey
import src.vault.api_paths as api_paths


@dataclass
class VaultClient:
    url: str = field(init=False, default=config.VAULT_ADDRESS)
    auth_path: str = field(init=False, default=config.VAULT_APP_ROLE_LOGIN_PATH)
    access_token: str = field(init=False)

    def __post_init__(self):
        self.__login()

    def __login(self):
        url = api_paths.LOGIN_PATH.format(
            VAULT_ADDRESS=self.url,
            API_VERSION=api_paths.API_VERSION,
            AUTH_PATH=self.auth_path,
        )
        payload = {
            "role_id": config.VAULT_APP_ROLE_ROLE_ID,
            "secret_id": config.VAULT_APP_ROLE_SECRET_ID,
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        logging.info("Successfully authenticated with Vault at address '%s'", self.url)

        self.access_token = response.json()["auth"]["client_token"]

    def get_key(self, key_path: str) -> KeyVaultKey | None:
        response = requests.get(
            api_paths.KV_PATH.format(
                VAULT_ADDRESS=self.url,
                API_VERSION=api_paths.API_VERSION,
                KV_PATH=f"{key_path}",
            ),
            headers={"X-Vault-Token": self.access_token},
        )
        try:
            response.raise_for_status()
        except requests.HTTPError:
            logging.error(
                f"Failed to get key {key_path}: status code: {response.status_code}"
            )
            return None
        logging.info(f"Successfully retrieved key {key_path} from vault")
        return KeyVaultKey(path=key_path, properties=response.json())

    def create_or_update_key(
        self, key_path: str, payload: dict[str, str]
    ) -> None:
        try:
            response = requests.post(
                api_paths.KV_PATH.format(
                    VAULT_ADDRESS=self.url,
                    API_VERSION=api_paths.API_VERSION,
                    KV_PATH=f"{key_path}",
                ),
                headers={"X-Vault-Token": self.access_token},
                json=payload,
            )
            response.raise_for_status()
            json_response = response.json()
        except Exception as e:
            logging.error(f"Error creating/updating key {key_path}: {e}")
        else:
            logging.info(
                f"Successfully created/updated key {key_path}. Current version: {json_response.get('data', {}).get('version', 'unknown')}"
            )


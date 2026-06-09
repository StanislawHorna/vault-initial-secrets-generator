import json
import logging
from src.JsonLogFormatter import JsonFormatter
from src.vault.VaultClient import VaultClient
from src.VaultKeyConfiguration import VaultKeyConfiguration
import src.config as config


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logging.basicConfig(
    level=config.LOG_LEVEL,
    handlers=[handler],
)

def main():
    client = VaultClient()
    parsed = json.loads(config.SECRETS_RAW)
    kv_key_configs = [VaultKeyConfiguration(**item) for item in parsed]
    for key_config in kv_key_configs:
        vault_key = client.get_key(key_config.path)
        if vault_key is None:
            logging.info(f"Key {key_config.path} does not exist in vault")
            client.create_or_update_key(key_config.path, key_config.get_payload())
            continue

        if key_config == vault_key:
            logging.info(f"Key {key_config.path} is up to date, no action needed")
            continue

        logging.info(f"Key {key_config.path} needs to be updated")
        client.create_or_update_key(key_config.path, key_config.get_payload())


if __name__ == "__main__":
    logging.info("Application started")
    main()

import logging
from dataclasses import dataclass, field
import random
import string

from src.vault.KeyVault import KeyVaultKeyProperty
import src.config as config

KEY_PATH_PATTERN_NO_SERVICE_HOSTNAME = "{kv_name}/data/{kv_name_prefix}/{key_name}"
KEY_PATH_PATTERN = "{kv_name}/data/{kv_name_prefix}/{service_hostname}/{key_name}"


@dataclass
class SecretProperty:
    name: str = field(init=True)
    value: str = field(init=True, default="")
    value_prefix: str = field(init=True, default="")
    value_length: int = field(init=True, default=0)
    value_section_separator: str = field(init=True, default="-")

    is_dynamic: bool = field(init=True, default=False)

    def __post_init__(self):
        if self.value == "":
            self.is_dynamic = True

    def __eq__(self, other):
        if not isinstance(other, KeyVaultKeyProperty):
            return NotImplemented

        if self.is_dynamic:
            return self.__compare_dynamic_value(other)
        
        return self.__compare_static_value(other)

    def __compare_dynamic_value(self, other):
        if not self.is_dynamic:
            return False

        self.value = other.value
        section_separator_len = (
            len(self.value_section_separator) if self.value_prefix != "" else 0
        )
        check = (
            other.value.startswith(self.value_prefix)
            and len(other.value)
            == len(self.value_prefix) + self.value_length + section_separator_len
        )
        if check:
            logging.info(f"Dynamic property '{self.name}' value format is correct")
            return True

        logging.warning(f"Dynamic property '{self.name}' value format is incorrect")
        if config.RECREATE_IF_DYNAMIC_VALUE_MISMATCH:
            logging.warning(
                "RECREATE_IF_DYNAMIC_VALUE_MISMATCH is set to true, will recreate the key to update the dynamic value"
            )
            return False
        return True

    def __compare_static_value(
        self, other
    ):
        check = self.value == other.value
        logging.info(f"Static property '{self.name}' comparison result: {check}")
        if check:
            return True
        logging.warning(f"Static property '{self.name}' value mismatch")
        return False

    def get_value(self, generate_new_if_dynamic_value: bool = False) -> str:

        # If value is not dynamic, return it as is
        if not self.is_dynamic:
            logging.info(f"Using static value for property '{self.name}'")
            return self.value

        # If value is dynamic and not empty,
        # this means that the value was fetched from vault and should be reused to avoid unnecessary updates
        if self.value != "" and not generate_new_if_dynamic_value:
            logging.info(f"Reusing existing value for dynamic property '{self.name}'")
            return self.value

        logging.info(f"Generating new value for dynamic property '{self.name}'")
        random_part = (
            self.value_prefix + self.value_section_separator
            if self.value_prefix != ""
            else ""
        )
        random_part += "".join(
            random.choices(string.ascii_letters + string.digits, k=self.value_length)
        )
        return random_part

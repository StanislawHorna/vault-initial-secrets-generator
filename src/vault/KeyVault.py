from dataclasses import dataclass, field


@dataclass
class KeyVaultKeyProperty:
    name: str = field(init=True)
    value: str = field(init=True)


@dataclass
class KeyVaultKey:
    path: str = field(init=True)
    properties: dict = field(init=True, default_factory=dict)

    def __post_init__(self):
        self.properties = {
            k: KeyVaultKeyProperty(name=k, value=v)
            for k, v in self.properties.get("data", {}).get("data", {}).items()
        }

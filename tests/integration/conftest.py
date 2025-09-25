import dataclasses as dc
from collections.abc import Generator
from pathlib import Path
from typing import Self

import pytest
from testcontainers.core.image import DockerImage
from testcontainers.core.wait_strategies import HttpWaitStrategy
from testcontainers.nginx import DockerContainer


@dc.dataclass(frozen=True, slots=True)
class ProxyDetails:
    host: str
    port: int


@pytest.fixture(scope="session")
def auth_credentials() -> dict[str, str]:
    return {"username": "userfoo", "password": "passbar"}


class ReverseNginxContainer(DockerContainer):
    def __init__(self, image: str, port: int = 80, **kwargs) -> None:
        super().__init__(
            image,
            _wait_strategy=HttpWaitStrategy(port=port).with_basic_credentials("userfoo", "passbar"),
            **kwargs,
        )
        self.port = port
        self.with_exposed_ports(self.port)

    def start(self) -> Self:
        super().start()

        return self


@pytest.fixture(scope="session")
def proxy_server() -> Generator[ProxyDetails]:
    cwd = Path(__file__).parent
    image_path = cwd / "docker"

    with DockerImage(path=image_path) as image:
        with ReverseNginxContainer(image=str(image)) as nginx:
            host = nginx.get_container_host_ip()
            port = nginx.get_exposed_port(80)
            yield ProxyDetails(host=host, port=int(port))

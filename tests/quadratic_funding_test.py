import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    get_localnet_default_account,
)
from algosdk.v2client.algod import AlgodClient

from smart_contracts.quadratic_funding import contract as quadratic_funding_contract


@pytest.fixture(scope="session")
def quadratic_funding_app_spec(algod_client: AlgodClient) -> ApplicationSpecification:
    return quadratic_funding_contract.app.build(algod_client)


@pytest.fixture(scope="session")
def quadratic_funding_client(
    algod_client: AlgodClient, quadratic_funding_app_spec: ApplicationSpecification
) -> ApplicationClient:
    client = ApplicationClient(
        algod_client,
        app_spec=quadratic_funding_app_spec,
        signer=get_localnet_default_account(algod_client),
    )
    client.create()
    return client


def test_says_hello(quadratic_funding_client: ApplicationClient) -> None:
    result = quadratic_funding_client.call(quadratic_funding_contract.hello, name="World")

    assert result.return_value == "Hello, World"

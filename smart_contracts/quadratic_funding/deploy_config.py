import logging
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
import algokit_utils

logger = logging.getLogger(__name__)

# Define deployment behavior based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    # Import the QuadraticFunding client class
    from smart_contracts.artifacts.quadratic_funding.client import QuadraticFundingClient

    # Initialize the QuadraticFunding client
    app_client = QuadraticFundingClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    # Deploy the Quadratic Funding smart contract
    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )

    app_client.start_funding_round()

    logger.info(
        f"Started funding round on {app_spec.contract.name} ({app_client.app_id})"
    )

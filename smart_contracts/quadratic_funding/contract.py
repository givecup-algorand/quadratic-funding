from beaker import Application, GlobalStateValue, LocalStateValue
from pyteal import (
    Seq, Assert, Approve, Bytes, Int, Txn, Global, TxnType, abi, TealType, Addr, If, Or, Expr, Concat, Sqrt
)

# Define global and local state for tracking donations and organizations
class GlobalState:
    funding_round_active = GlobalStateValue(stack_type=TealType.uint64, default=Int(0))
    owner = GlobalStateValue(stack_type=TealType.bytes, default=Bytes(""))
    organizations = [GlobalStateValue(stack_type=TealType.bytes, default=Bytes("")) for _ in range(10)]
    matching_funds = [GlobalStateValue(stack_type=TealType.uint64, default=Int(0)) for _ in range(10)]

class LocalState:
    user_donations = LocalStateValue(stack_type=TealType.uint64, default=Int(0))
    user_organization_donations = LocalStateValue(stack_type=TealType.bytes, default=Bytes(""))

app = Application("QuadraticFunding", state=GlobalState(), local_state=LocalState())

@app.create
def create():
    return Seq(
        app.state.funding_round_active.set(Int(0)),
        app.state.owner.set(Txn.sender()),
        Approve()
    )

# Owner functions 

@app.external
def start_funding_round() -> Expr:
    """
    Start a funding round. Only callable by the owner.
    """
    return Seq(
        Assert(Txn.sender() == app.state.owner),
        app.state.funding_round_active.set(Int(1)),
        Approve()
    )

@app.external
def end_funding_round() -> Expr:
    """
    End the current funding round. Only callable by the owner.
    """
    return Seq(
        Assert(Txn.sender() == app.state.owner),
        app.state.funding_round_active.set(Int(0)),
        Approve()
    )

@app.external
def add_organization(organization: abi.Address) -> Expr:
    """
    Add an organization address. Only callable by the owner.
    """
    is_owner = Txn.sender() == app.state.owner.get()

    # Logic to add organization
    for i in range(len(app.state.organizations)):
        org = app.state.organizations[i].get()
        add_org = Seq(app.state.organizations[i].set(organization.get()))
        if org == Bytes(""):
            break

    return Seq(
        Assert(is_owner),
        add_org,
        Approve()
    )

# User functions

@app.external
def donate(organization: abi.Address, amount: abi.Uint64) -> Expr:
    """
    Handle donations to organizations during active funding rounds.
    """
    is_funding_round_active = app.state.funding_round_active.get() == Int(1)
    is_valid_organization = Or(
        *[app.state.organizations[i].get() == organization.get() for i in range(len(app.state.organizations))]
    )

    user_donation_key = Concat(Bytes("donation_"), Txn.sender(), Bytes("_"), organization.get())

    update_user_donation = Seq(
        app.local[user_donation_key].set(app.local[user_donation_key].get() + amount.get()),
        # Update other necessary state variables
    )

    return Seq(
        Assert(is_funding_round_active),
        Assert(is_valid_organization),
        update_user_donation,
        Approve()
    )


@app.external
def calculate_matching_funds() -> Expr:
    """
    Calculate and allocate matching funds to each organization.
    This should be called after a funding round ends.
    """
    total_square_of_sums = Int(0)
    individual_squares = [Int(0) for _ in range(len(app.state.organizations))]

    # Calculate the square of the sum of square roots of individual donations
    for i in range(len(app.state.organizations)):
        total_donations = app.state.organizations[i].amount
        individual_squares[i] = Sqrt(total_donations)
        total_square_of_sums += individual_squares[i] * individual_squares[i]

    # Calculate matching funds for each organization
    update_matching_funds_ops = []
    for i in range(len(app.state.organizations)):
        matching_funds = (individual_squares[i] * individual_squares[i]) / total_square_of_sums
        update_matching_funds_ops.append(app.state.matching_funds[i].set(matching_funds))

    return Seq(
        update_matching_funds_ops,
        Approve()
    )

# storage functions

@app.external(read_only=True)
def get_total_donations_for_organization(organization: abi.Address, *, output: abi.Uint64) -> Expr:
    """
    Retrieve the total donations made to a specific organization.
    """
    total_donations = Int(0)
    for i in range(len(app.state.organizations)):
        org = app.state.organizations[i].get()
        total_donations = If(org == organization.get(), 
                             app.state.organizations[i].amount, 
                             total_donations)
    return output.set(total_donations)


@app.external(read_only=True)
def get_user_donation_to_organization(user: abi.Address, organization: abi.Address, *, output: abi.Uint64) -> Expr:
    """
    Retrieve the amount donated by a specific user to a specific organization.
    """
    user_donation_key = Concat(Bytes("donation_"), user.get(), Bytes("_"), organization.get())
    return output.set(app.local.get(user_donation_key, TealType.uint64))


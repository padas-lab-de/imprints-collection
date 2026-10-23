import pytest

from ic.utils.address_utils import has_address


@pytest.mark.parametrize(
    "address",
    [None, {}, [], "text", {"street": "", "city": None}, {"street": "  ", "zip": ""}],
)
def test_empty_address(address):
    assert not has_address(address)


@pytest.mark.parametrize(
    "address",
    [{"city": "Passau"}, {"street": "", "city": "Passau"}, {"zip": 94032}],
)
def test_non_empty_address(address):
    assert has_address(address)

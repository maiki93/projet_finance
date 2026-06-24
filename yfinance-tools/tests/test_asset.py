from yfinance_tools.domain import Asset, AssetType


# to delete
def test_asset_construction():

    asset1 = Asset("toto", AssetType["INDEX"])
    assert asset1.name == "toto"
    assert asset1.type == AssetType.INDEX


# test a Factory of Assets ()
# def test_create_list_of_all_assets():

#     assets = get_assets()
#     assert len(assets) == 5

"""
Validation of static data identifiers read from a file,
use by InFileIdentifierRegistry

Basic types dto are combined to respect requirements for this adapter
"""

from pydantic import BaseModel, ConfigDict, TypeAdapter

from yfinance_tools.domain import AssetType

from .basic_types_dto import AssetNameDto, AssetTypeDto, IsinDto


class RegistryFileEntryDto(BaseModel):
    """
    A whole entry is validated if all conditions are satisfied:
    - yfTicker is present : required string
    - assetType is valid or None : rejected if not convertible to AssetType
    - isin has a valid format (ISO 6166) or None: rejected format is not valid

    - extra key in dictionary are forbidden
    """

    model_config = ConfigDict(extra="forbid")

    yfTicker: str
    assetType: AssetTypeDto = AssetType.UNDEFINED
    currency: str | None = None
    isin: IsinDto | None = None


"""Match the json file format expected by the Registry file implemantation"""
RegistryFileDto = TypeAdapter(dict[AssetNameDto, RegistryFileEntryDto])

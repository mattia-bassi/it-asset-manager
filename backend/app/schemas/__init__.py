from app.schemas.site import Site, SiteCreate, SiteUpdate, SiteList
from app.schemas.person import Person, PersonCreate, PersonUpdate, PersonList, PersonWithSite, PersonMerge
from app.schemas.asset_type import AssetType, AssetTypeCreate, AssetTypeUpdate, AssetTypeList, AssetTypeWithParent
from app.schemas.asset import Asset, AssetCreate, AssetUpdate, AssetList, AssetWithDetails
from app.schemas.inventory_sku import InventorySku, InventorySkuCreate, InventorySkuUpdate, InventorySkuList, InventorySkuQuantityUpdate
from app.schemas.assignment_item import AssignmentItem, AssignmentItemCreate
from app.schemas.assignment import Assignment, AssignmentCreate, AssignmentUpdate, AssignmentList, AssignmentWithDetails
from app.schemas.document_template import (
    DocumentTemplate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentTemplateInDB
)
from app.schemas.sim import (
    SimStatus,
    SimBase,
    SimCreate,
    SimUpdate,
    SimResponse,
    SimWithCredentials,
    SimListResponse
)
from app.schemas.badge import (
    Badge,
    BadgeCreate,
    BadgeUpdate,
    BadgeList,
    BadgeStatus,
    BadgeType
)

__all__ = [
    "Site", "SiteCreate", "SiteUpdate", "SiteList",
    "Person", "PersonCreate", "PersonUpdate", "PersonList", "PersonWithSite", "PersonMerge",
    "AssetType", "AssetTypeCreate", "AssetTypeUpdate", "AssetTypeList", "AssetTypeWithParent",
    "Asset", "AssetCreate", "AssetUpdate", "AssetList", "AssetWithDetails",
    "InventorySku", "InventorySkuCreate", "InventorySkuUpdate", "InventorySkuList", "InventorySkuQuantityUpdate",
    "AssignmentItem", "AssignmentItemCreate",
    "Assignment", "AssignmentCreate", "AssignmentUpdate", "AssignmentList", "AssignmentWithDetails",
    "DocumentTemplate", "DocumentTemplateCreate", "DocumentTemplateUpdate", "DocumentTemplateInDB",
    "SimStatus", "SimBase", "SimCreate", "SimUpdate", "SimResponse", "SimWithCredentials", "SimListResponse",
    "Badge", "BadgeCreate", "BadgeUpdate", "BadgeList", "BadgeStatus", "BadgeType"
]


from pydantic import BaseModel


class ModuleCreateRequest(BaseModel):
    """Request to create privileges and role_privilege mappings for a module"""

    module_name: str


class ModuleUpdateRequest(BaseModel):
    """Request to update privileges for a module"""

    module_name: str


class ModuleDeleteRequest(BaseModel):
    """Request to delete privileges and role_privilege mappings for a module"""

    module_name: str

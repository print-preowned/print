from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.privilege.model import PrivilegeCreateRequest, PrivilegeUpdateRequest
from app.role_privilege.model import RolePrivilegeCreateRequest


class ModuleCreateRequest(BaseModel):
    """Request to create privileges and role_privilege mappings for a module"""
    module_name: str


class ModuleUpdateRequest(BaseModel):
    """Request to update privileges for a module"""
    module_name: str


class ModuleDeleteRequest(BaseModel):
    """Request to delete privileges and role_privilege mappings for a module"""
    module_name: str


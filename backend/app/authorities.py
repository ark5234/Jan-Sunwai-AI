from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class AuthorityLevel(str, Enum):
    LOCAL = "Local Municipal Authority"
    STATE = "State/Utility Provider"
    SAFETY = "Safety & Law Enforcement"
    APEX = "Apex & Oversight Body"

class Authority(BaseModel):
    id: str
    name: str # e.g. "Public Works Department"
    level: AuthorityLevel
    domain: str # e.g. "Roads & Civil Works"
    escalation_days: int = 21
    parent_authority_id: Optional[str] = None # For escalation

# Predefined Authorities Database
AUTHORITIES_DB = [
    # --- 1. Local Municipal Authorities ---
    Authority(
        id="MUNI_PWD",
        name="Public Works Department (PWD)",
        level=AuthorityLevel.LOCAL,
        domain="Roads, Bridges, Civil Repairs",
        escalation_days=21,
        parent_authority_id="STATE_CMO"
    ),
    Authority(
        id="MUNI_SANITATION",
        name="Sanitation & Solid Waste Mgmt",
        level=AuthorityLevel.LOCAL,
        domain="Garbage, Public Toilets, Cleaning",
        escalation_days=7,
        parent_authority_id="STATE_CMO"
    ),
    Authority(
        id="MUNI_HORTICULTURE",
        name="Horticulture Department",
        level=AuthorityLevel.LOCAL,
        domain="Parks, Trees, Greenery",
        escalation_days=14,
        parent_authority_id="STATE_CMO"
    ),
    Authority(
        id="MUNI_LIGHTING",
        name="Street Lighting Dept",
        level=AuthorityLevel.LOCAL,
        domain="Street Lights, Electrical Poles",
        escalation_days=7,
        parent_authority_id="UTIL_DISCOM" # Escalate to DISCOM maybe? Or CMO by default.
    ),
    Authority(
        id="MUNI_WATER",
        name="Water Supply & Sewerage Board",
        level=AuthorityLevel.LOCAL,
        domain="Water Supply, Drainage, Sewerage",
        escalation_days=10,
        parent_authority_id="STATE_CMO"
    ),

    # --- 2. Specialized Utility & State Providers ---
    Authority(
        id="UTIL_DISCOM",
        name="Power Distribution Company (DISCOM)",
        level=AuthorityLevel.STATE,
        domain="High Voltage Power, Transformers, Grid",
        escalation_days=3, # Hazardous issues need faster checks
        parent_authority_id="STATE_CMO"
    ),
    Authority(
        id="UTIL_TRANSPORT",
        name="State Transport Corporation",
        level=AuthorityLevel.STATE,
        domain="Buses, Terminals",
        escalation_days=14,
        parent_authority_id="STATE_CMO"
    ),
    Authority(
        id="UTIL_PCB",
        name="Pollution Control Board",
        level=AuthorityLevel.STATE,
        domain="Industrial Waste, Smoke, Chemical Pollution",
        escalation_days=14,
        parent_authority_id="CENTRAL_DARPG"
    ),

    # --- 3. Safety & Law Enforcement ---
    Authority(
        id="POLICE_LOCAL",
        name="Local Police Station (SHO)",
        level=AuthorityLevel.SAFETY,
        domain="Law & Order, Illegal Parking, Nuisance",
        escalation_days=3,
        parent_authority_id="STATE_HOME_DEPT"
    ),
    Authority(
        id="POLICE_TRAFFIC",
        name="Traffic Police",
        level=AuthorityLevel.SAFETY,
        domain="Traffic Signals, Obstructions",
        escalation_days=3,
        parent_authority_id="STATE_HOME_DEPT"
    ),

    # --- 4. Apex & Oversight Bodies ---
    Authority(
        id="STATE_CMO",
        name="Chief Minister's Office (Grievance Cell)",
        level=AuthorityLevel.APEX,
        domain="State Level Oversight",
        escalation_days=30,
        parent_authority_id="CENTRAL_DARPG"
    ),
    Authority(
        id="CENTRAL_DARPG",
        name="DARPG (Central Govt)",
        level=AuthorityLevel.APEX,
        domain="National Oversight",
        escalation_days=60
    )
]

def get_authority_by_id(auth_id: str) -> Optional[Authority]:
    for auth in AUTHORITIES_DB:
        if auth.id == auth_id:
            return auth
    return None

def get_authorities_by_level(level: AuthorityLevel) -> List[Authority]:
    return [auth for auth in AUTHORITIES_DB if auth.level == level]

# Mapping from Classifier Output to Authority ID
CLASSIFIER_TO_AUTHORITY_MAP = {
    # 1. Local Municipal Authorities
    "Municipal - PWD (Roads)": "MUNI_PWD",
    "Municipal - PWD (Bridges)": "MUNI_PWD",
    
    "Municipal - Sanitation": "MUNI_SANITATION",
    
    "Municipal - Horticulture": "MUNI_HORTICULTURE",
    
    "Municipal - Street Lighting": "MUNI_LIGHTING",
    
    "Municipal - Water & Sewerage": "MUNI_WATER",
    
    # 2. Specialized Utility
    "Utility - Power (DISCOM)": "UTIL_DISCOM",
    
    "State Transport": "UTIL_TRANSPORT",
    
    "Pollution Control Board": "UTIL_PCB",
    
    # 3. Safety & Law Enforcement
    "Police - Local Law Enforcement": "POLICE_LOCAL",
    "Police - Traffic": "POLICE_TRAFFIC",
    
    # Fallbacks/Generic
    "Civil Engineering Dept": "MUNI_PWD",
    "Sanitation Dept": "MUNI_SANITATION",
    "Horticulture Dept": "MUNI_HORTICULTURE",
    "Electricity Dept": "MUNI_LIGHTING", # Or UTIL_DISCOM depending on severity? Default to Municipal for lights.
    "Drainage Dept": "MUNI_WATER",
    "Pollution Control Dept": "UTIL_PCB",
    "Enforcement Dept": "POLICE_LOCAL"
}

def get_authority_id_from_dept_string(dept_string: str) -> Optional[str]:
    return CLASSIFIER_TO_AUTHORITY_MAP.get(dept_string)

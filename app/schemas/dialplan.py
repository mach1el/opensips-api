from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ItemIn(BaseModel):
  did: str = Field(..., min_length=1)

class ItemOut(BaseModel):
  did: str
  special_did: bool

class DialplanEntry(BaseModel):
  dpid: int = Field(..., description="Dialplan ID (integer)")
  pr: int = Field(..., description="Priority")
  match_op: int = Field(..., description="Match operation (OpenSIPS match operator)")
  match_exp: str = Field(..., description="Matching expression (regex or string)")
  match_flags: Optional[int] = Field(0, description="Flags for matching operation")
  subst_exp: Optional[str] = Field(None, description="Substitution expression")
  repl_exp: Optional[str] = Field(None, description="Replacement expression")
  timerec: Optional[str] = Field(None, description="Time recursion string")
  disabled: bool = Field(False, description="Disabled flag")
  attrs: Optional[str] = Field(
    None,
    description="Optional attributes string as stored in OpenSIPS dialplan.attrs"
  )

class DialplanEntriesRequest(BaseModel):
  entries: List[DialplanEntry]

class DialplanRuleOut(DialplanEntry):
  id: int = Field(..., description="Primary key of dialplan row")
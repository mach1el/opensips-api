from typing import List
from fastapi import APIRouter, HTTPException, status
from app.services import (
  is_special_did,
  insert_dialplan_entries,
  fetch_all_dialplan_rules,
  delete_dialplan_rule
)
from app.schemas import (
  ItemIn, 
  ItemOut,
  DialplanEntriesRequest, 
  DialplanRuleOut
)

router = APIRouter()

@router.post("/checkdids", response_model=ItemOut, status_code=201)
async def check_dids(body: ItemIn):
  special = is_special_did(body.did)
  return ItemOut(did=body.did, special_did=special)

@router.post("/add", status_code=201)
async def add_dialplan(payload: DialplanEntriesRequest):
  result = await insert_dialplan_entries(payload.entries)
  return {
    "status": "ok",
    "inserted": result["inserted"],
    "mi": result["mi_response"],
  }

@router.get("/fetchall", response_model=List[DialplanRuleOut])
async def fetch_all():
  return await fetch_all_dialplan_rules()

@router.delete("/delete/{rule_id}")
async def delete_rule(rule_id: int):
  result = await delete_dialplan_rule(rule_id)

  if result["deleted"] == 0:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Dialplan rule not found",
    )

  return {
    "status": "ok",
    "deleted": 1,
    "mi": result["mi_response"],
  }
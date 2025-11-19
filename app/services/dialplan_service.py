from typing import Sequence, Any, Dict, List, Tuple
from app.services.db import get_db_pool
from app.services.opensips_mi import mi_execute
from app.schemas import (
  DialplanEntry,
  DialplanRuleOut
)

MI_COMMAND = "dp_reload"

async def is_special_did(did: str) -> bool:
  """
  Return True if DID exactly equals a row in dialplan.match_exp
  """
  pool = await get_db_pool()

  sql = """
    SELECT EXISTS (
      SELECT 1
      FROM dialplan
      WHERE match_exp = $1
    )
  """

  async with pool.acquire() as conn:
    row = await conn.fetchval(sql, did)

  return bool(row)

async def insert_dialplan_entries(entries: Sequence[DialplanEntry]) -> Dict[str, Any]:
  """
  Insert multiple dialplan rows into the database.
  Returns number of inserted rows.
  """
  if not entries:
     return {"inserted": 0, "skipped": 0, "mi_response": None}

  unique_map: Dict[Tuple[int, str], DialplanEntry] = {}
  for e in entries:
    key = (e.dpid, e.match_exp)
    if key not in unique_map:
      unique_map[key] = e

  unique_entries: List[DialplanEntry] = list(unique_map.values())
  dpids = sorted({e.dpid for e in unique_entries})

  pool = await get_db_pool()

  sql_existing = """
    SELECT dpid, match_exp
    FROM dialplan
    WHERE dpid = ANY($1::int[])
  """

  async with pool.acquire() as conn:
    rows = await conn.fetch(sql_existing, dpids)

  existing_pairs = {(r["dpid"], r["match_exp"]) for r in rows}

  new_entries: List[DialplanEntry] = [
    e for e in unique_entries
    if (e.dpid, e.match_exp) not in existing_pairs
  ]

  skipped_count = len(entries) - len(new_entries)

  if not new_entries:
    # Nothing new to insert → no MI reload
    return {
      "inserted": 0,
      "skipped": skipped_count,
      "mi_response": None,
    }

  sql = """
    INSERT INTO dialplan (
      dpid,
      pr,
      match_op,
      match_exp,
      match_flags,
      subst_exp,
      repl_exp,
      timerec,
      disabled,
      attrs
    )
    VALUES (
      $1, $2, $3, $4, $5,
      $6, $7, $8, $9, $10
    )
  """

  values = [
    (
      e.dpid,
      e.pr,
      e.match_op,
      e.match_exp,
      e.match_flags,
      e.subst_exp,
      e.repl_exp,
      e.timerec,
      e.disabled,
      e.attrs,
    )
    for e in entries
  ]

  async with pool.acquire() as conn:
    await conn.executemany(sql, values)

  mi_response = await mi_execute(MI_COMMAND)

  return {
    "inserted": len(new_entries),
    "skipped": skipped_count,
    "mi_response": mi_response,
  }

async def fetch_all_dialplan_rules() -> List[DialplanRuleOut]:
  pool = await get_db_pool()

  sql = """
    SELECT
      id,
      dpid,
      pr,
      match_op,
      match_exp,
      match_flags,
      subst_exp,
      repl_exp,
      timerec,
      disabled,
      attrs
    FROM dialplan
    ORDER BY dpid, pr, id
  """

  async with pool.acquire() as conn:
    rows = await conn.fetch(sql)

  return [
    DialplanRuleOut(
      id=row["id"],
      dpid=row["dpid"],
      pr=row["pr"],
      match_op=row["match_op"],
      match_exp=row["match_exp"],
      match_flags=row["match_flags"],
      subst_exp=row["subst_exp"],
      repl_exp=row["repl_exp"],
      timerec=row["timerec"],
      disabled=row["disabled"],
      attrs=row["attrs"],
    )
    for row in rows
  ]

async def delete_dialplan_rule(rule_id: int) -> Dict[str, Any]:
  """
  Delete a dialplan row by primary key id.
  If a row was deleted, trigger OpenSIPS dp_reload.
  Returns:
    {
      "deleted": 0 or 1,
      "mi_response": <dict or None>
    }
  """
  pool = await get_db_pool()

  async with pool.acquire() as conn:
    row = await conn.fetchrow(
      "DELETE FROM dialplan WHERE id = $1 RETURNING id",
      rule_id,
    )

  if row is None:
    # nothing deleted, don't call MI
    return {"deleted": 0, "mi_response": None}

  mi_response = await mi_execute(MI_COMMAND)

  return {
    "deleted": 1,
    "mi_response": mi_response,
  }
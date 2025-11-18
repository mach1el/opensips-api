# OpenSIPS Dialplan API

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![OpenSIPS](https://img.shields.io/badge/OpenSIPS-MI%20JSON--RPC-0E6E3A?style=for-the-badge)

FastAPI service that manages **OpenSIPS dialplan rules** in PostgreSQL and triggers
**OpenSIPS MI JSON-RPC** to reload the dialplan after changes.

The service is designed to:

- Store and manage dialplan rules in a central PostgreSQL database
- Check if an incoming DID is marked as a **special DID**
- Expose simple REST APIs to:
  - Add one or many dialplan rules
  - List all existing rules
  - Delete rules by ID
- Automatically call OpenSIPS MI (`dp_reload`) after insert/delete operations
---

## Architecture Overview

```text
+-------------+        HTTP/JSON        +------------------+       MI JSON-RPC       +-------------+
|   Client    |  <--------------------> |  Dialplan API    |  <------------------->  |  OpenSIPS   |
|  (Portal)   |   /api/v1/dialplan/*    |  (FastAPI)       |   POST /mi dp_reload   |  Proxy       |
+-------------+                         +------------------+                         +-------------+
                                               |
                                               | asyncpg
                                               v
                                         +-----------+
                                         | Postgres  |
                                         | dialplan  |
                                         +-----------+
```

---

## Quick Start

### Configuration

All configuration uses environment variables (e.g. injected via Docker or
Kubernetes).

### PostgreSQL

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=opensips
POSTGRES_PASSWORD=secret
POSTGRES_DB=opensips
```

### OpenSIPS MI

```env
OPENSIPS_MI_HOST=opensips
OPENSIPS_MI_PORT=8787
```

Validation:

- `OPENSIPS_MI_HOST` must be non-empty.
- `OPENSIPS_MI_PORT` must be between `1` and `65535`.

### Application

```env
PORT=3000        # uvicorn port
```

### Run with Docker

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends   build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ARG PORT=3000
ENV PORT=${PORT}
EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
```

`requirements.txt` (example):
```
asyncpg
fastapi
uvicorn[standard]
pydantic-settings
python-multipart
httpx
pytest
psycopg2
```

`docker compose`:
```yaml
services:
  opensips-api:
    build:
      context: .
      args:
        PORT: 3000
    environment:
      POSTGRES_HOST: pg-opensips
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test
      POSTGRES_PORT: 5432
      DB_POOL_SIZE: 5
      DB_MAX_OVERFLOW: 10
      OPENSIPS_MI_HOST: localhost
      OPENSIPS_MI_PORT: 8787
    command: uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
    ports:
      - "3000:3000"
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: opensips
      POSTGRES_USER: opensips
      POSTGRES_PASSWORD: opensips
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U opensips -d opensips"]
      interval: 5s
      timeout: 3s
      retries: 10
```

---

## Dialplan Model

Internally, each dialplan rule is represented as:

```json
{
  "id": 1,                         // server-generated, only in responses
  "dpid": 1,
  "pr": 10,
  "match_op": 1,
  "match_exp": "^\+3906.*$",
  "match_flags": "0",
  "subst_exp": "^.*$",
  "repl_exp": "sip.example.org:5060",
  "timerec": null,
  "disabled": false,
  "attrs": null
}
```

Fields:

| Column        | Type (OpenSIPS) | Type (PostgreSQL, suggested)              | Description                                                                                                                                                                                                            |
| ------------- | --------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | `unsigned int`  | `SERIAL` / `BIGSERIAL`                    | Auto-increment **primary key**, unique identifier for each rule. ([openSIPS][1])                                                                                                                                       |
| `dpid`        | `int`           | `INTEGER`                                 | **Dialplan ID** – logical group of rules. This is the `dpid` you pass to `dp_translate()` or MI commands. ([openSIPS][1])                                                                                              |
| `pr`          | `int`           | `INTEGER`                                 | **Priority** of the rule within a given `dpid`. Lower values are evaluated first. Default `0`. ([openSIPS][1])                                                                                                         |
| `match_op`    | `int`           | `INTEGER`                                 | **Match operator**: `0` = exact string match, `1` = regular expression match. ([openSIPS][1])                                                                                                                          |
| `match_exp`   | `string(64)`    | `TEXT` / `VARCHAR(64)`                    | **Match expression** – either a plain string (for `match_op = 0`) or a regex (for `match_op = 1`). Typically applied to the called number / R-URI user. ([openSIPS][1])                                                |
| `match_flags` | `int`           | `INTEGER`                                 | **Matching flags** – `0` = case-sensitive, `1` = case-insensitive. (Internally treated as a bitmask; most dialplan rules use `0` or `1` only.) ([openSIPS][1])                                                         |
| `subst_exp`   | `string(64)`    | `TEXT` / `VARCHAR(64)`                    | **Substitution expression** – regex pattern used to capture parts of the input (e.g. `(.*)`), usually combined with `repl_exp`. Optional. ([openSIPS][1])                                                              |
| `repl_exp`    | `string(32)`    | `TEXT` / `VARCHAR(32)`                    | **Replacement expression** (sed-like) – how to rewrite the input using captured groups, e.g. `\1;user=phone` or a new R-URI/host. Optional. ([openSIPS][1])                                                            |
| `timerec`     | `string(255)`   | `TEXT`                                    | **Time recurrence** – limits when the rule is active (time ranges, days, etc.). Leave `NULL`/empty if the rule should apply **all the time**. ([openSIPS][1])                                                          |
| `disabled`    | `int`           | `INTEGER` (or mapped to `BOOLEAN` in API) | **Enable / disable flag** – `0` means rule is active; non-zero means the rule is disabled and should be ignored by the dialplan engine. ([openSIPS][1])                                                                |
| `attrs`       | `string(255)`   | `TEXT` or `JSONB`                         | **Attributes** – free-form string returned when the rule matches. Commonly used to store metadata (tags, routing hints). In this API, we expose it as a JSON object and serialize it into this column. ([openSIPS][1]) |

[1]: https://www.opensips.org/Documentation/Install-DBSchema-3-6 "openSIPS | Documentation / DB schema - 3.6 "

---

## API Endpoints

Base path: **`/api/v1/dialplan`**

### 1. Check DID is special

**POST** `/api/v1/dialplan/checkdids`

**Request Body**

```json
{
  "did": "+84XXXXXXXXX"
}
```

Checks if the given DID **exactly matches** any `match_exp` in the `dialplan` table.

- Uses `is_special_did(did)` under the hood.
- Returns a simple JSON with the result.

**Response example**

```json
{
  "did": "+84XXXXXXXXX",
  "special_did": true
}
```

---

### 2. Add one or many dialplan rules

**POST** `/api/v1/dialplan/add`

Inserts multiple dialplan entries into the `dialplan` table and then calls
OpenSIPS MI `dp_reload` via JSON-RPC.

**Request body**

```json
{
  "entries": [
    {
      "dpid": 1,
      "pr": 10,
      "match_op": 1,
      "match_exp": "^\+3906.*$",
      "match_flags": "0",
      "subst_exp": "^.*$",
      "repl_exp": "sip.example.org:5060",
      "timerec": "",
      "disabled": false,
      "attrs": {
        "tag": "special_did"
      }
    },
    {
      "dpid": 1,
      "pr": 20,
      "match_op": 1,
      "match_exp": "^0202[0-9]{3}$",
      "match_flags": "0",
      "subst_exp": "^.*$",
      "repl_exp": "sip.example.org:5060",
      "timerec": "",
      "disabled": false,
      "attrs": {
        "tag": "normal_did"
      }
    }
  ]
}
```

**Response example**

```json
{
  "status": "ok",
  "inserted": 2,
  "mi": {
    "jsonrpc": "2.0",
    "result": "OK",
    "id": "1"
  }
}
```

If MI returns an error, it is passed through:

```json
{
  "status": "ok",
  "inserted": 2,
  "mi": {
    "jsonrpc": "2.0",
    "error": {
      "code": -32601,
      "message": "Method not found"
    },
    "id": "1"
  }
}
```

> Note: data is written to DB regardless of MI result; MI response is only for visibility.

---

### 3. Fetch all dialplan rules

**GET** `/api/v1/dialplan/fetchall`

Returns all existing rows from the `dialplan` table.

**Response example**

```json
[
  {
    "id": 1,
    "dpid": 1,
    "pr": 10,
    "match_op": 1,
    "match_exp": "^\+3906.*$",
    "match_flags": "0",
    "subst_exp": "^.*$",
    "repl_exp": "sip.example.org:5060",
    "timerec": "",
    "disabled": false,
    "attrs": null
  },
  {
    "id": 2,
    "dpid": 1,
    "pr": 20,
    "match_op": 1,
    "match_exp": "^0202[0-9]{3}$",
    "match_flags": "0",
    "subst_exp": "^.*$",
    "repl_exp": "sip.example.org:5060",
    "timerec": "",
    "disabled": false,
    "attrs": null
  }
]
```

---

### 4. Delete a rule by ID

**DELETE** `/api/v1/dialplan/delete/{rule_id}`

Deletes a single row by `id` from the `dialplan` table.  
If a row was deleted, OpenSIPS MI `dp_reload` is called.

- If the rule does **not** exist → `404 Not Found`.

**Example**

```bash
curl -X DELETE http://localhost:3000/api/v1/dialplan/delete/3
```

**Response (deleted)**

```json
{
  "status": "ok",
  "deleted": 1,
  "mi": {
    "jsonrpc": "2.0",
    "result": "OK",
    "id": "1"
  }
}
```

**Response (not found)**

```json
{
  "detail": "Dialplan rule not found"
}
```

Cascading deletes for related tables (if any) are controlled via PostgreSQL
foreign keys with `ON DELETE CASCADE`.

---

## OpenSIPS MI Integration

The service calls OpenSIPS MI (JSON-RPC) with:

```bash
curl -X POST http://$OPENSIPS_MI_HOST:$OPENSIPS_MI_PORT/mi -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"1","method":"dp_reload"}'
```

This is implemented via `httpx`:

- URL: `http://OPENSIPS_MI_HOST:OPENSIPS_MI_PORT/mi`
- Body:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "dp_reload"
}
```

Responses are proxied back to the caller of `/add` or `/delete/{id}`.

---

## cURL examples

```bash
curl -X POST http://127.0.0.1:3000/api/v1/checkdids   -H "Content-Type: application/json"   -d '{"did":"+84112233000"}'
# {"did":"+84112233000","special_did":true}

curl -X POST http://127.0.0.1:3000/api/v1/checkdids   -H "Content-Type: application/json"   -d '{"did":"+84112233001"}'
# {"did":"+84112233001","special_did":false}
```

---

## Deployment Notes

- **Port flexibility**: use `-e PORT=8080 -p 8080:8080` (Dockerfile expands `${PORT}` at runtime).  
- **DB connectivity**: ensure network reachability to your OpenSIPS DB (K8s service / Compose network).  
- **Logging**: set `LOG_LEVEL=DEBUG` during onboarding; keep `INFO` in prod.  
- **CORS**: expose only to your internal UIs (`ALLOW_ORIGINS=https://ops.tools.local`).  

---

## OpenSIPS Integration

This service is designed to be called from **OpenSIPS** to decide routing for *special DIDs*.

> Tested with OpenSIPS 3.3+. It uses `rest_client` (or `http_client` if you need Basic Auth), `json` to parse the reply, and `htable` for a small in-memory cache.

### 1) Load modules & params

```cfg
#### modules
loadmodule "xlog.so"
loadmodule "json.so"
loadmodule "rest_client.so"   # or http_client.so if you need custom headers
loadmodule "htable.so"

#### cache: remember DID → 0/1 for 60s
modparam("htable", "htable", "sp=>size=8;autoexpire=60")

#### optional: rest_client tuning
# modparam("rest_client", "connection_timeout", 2)
# modparam("rest_client", "dns_try_ipv6", 0)

#### flag to mark special DIDs
#define FLT_SPECIAL 10
```
### 2) Get called DID (R-URI → To → P-Called-Party-ID)

```cfg
route[GET_CALLED_DID] {
  $var:did = $rU;
  if ($var:did == "") $var:did = $tU;

  # If provider sends P-Called-Party-ID, prefer it
  $var:pcpi = $(hdr(P-Called-Party-ID){re.subst,/.*<sip:([^@;>;]*)[>@;].*/\1/});
  if ($var:pcpi != "") $var:did = $var:pcpi;

  xlog("L_INFO", "DID candidate: $var:did\n");
  return;
}
```
### 3) Call the API with cache (no auth, using `rest_client`)

```cfg
route[CHECK_SPECIAL_DID] {
  route(GET_CALLED_DID);
  if ($var:did == "") return;

  # cache hit?
  if ($sht(sp=>$var:did) != $null) {
    if ($sht(sp=>$var:did) == 1) setflag(FLT_SPECIAL);
    return;
  }

  # call your service (use the docker service name or VIP)
  $var:url  = "http://opensips-api:3000/api/v1/checkdids";
  $var:body = "{\"did\":\"\"}";

  # inject DID value safely
  $var:body = $(var(body){re.subst,/""/\"" + $var:did + "\"/});

  rest_post($var:url, $var:body, "application/json",
            "$var:code", "$var:reason", "$var:ctype", "$var:resp");

  if ($var:code != 200) {
    xlog("L_ERR", "special-did API error $var:code $var:reason\n");
    $sht(sp=>$var:did) = 0;  # fail-open: not special
    return;
  }

  # parse minimal JSON: {"did":"...","special_did":true|false}
  json_get_field($var:resp, "special_did", "$var:is_special");

  if ($var:is_special == "true" || $var:is_special == 1) {
    setflag(FLT_SPECIAL);
    $sht(sp=>$var:did) = 1;
    append_hf("X-Special-DID: true\r\n");
  } else {
    $sht(sp=>$var:did) = 0;
  }
}
```
### 4) Use it in your main routing

```cfg
route {
  if (is_method("INVITE")) {
    route(CHECK_SPECIAL_DID);

    if (isflagset(FLT_SPECIAL)) {
      xlog("L_INFO", "Special DID -> VIP handling\n");
      route(VIP_ROUTE);   # define your VIP routing here
      exit;
    }
  }

  route(NORMAL_ROUTE);
}
```
### 5) If the API requires Basic Auth (use `http_client`)

```cfg
loadmodule "http_client.so"

route[CHECK_SPECIAL_DID] {
  route(GET_CALLED_DID);
  if ($var:did == "") return;

  if ($sht(sp=>$var:did) != $null) { if ($sht(sp=>$var:did) == 1) setflag(FLT_SPECIAL); return; }

  $var:url  = "http://opensips-api:3000/api/v1/checkdids";
  $var:body = "{\"did\":\"" + $var:did + "\"}";
  # base64("user:pass") below:
  $var:hdrs = "Content-Type: application/json\r\nAuthorization: Basic dXNlcjpwYXNz\r\n";

  http_request("POST", $var:url, $var:hdrs, $var:body, "$var:code", "$var:reason", "$var:resp");

  if ($var:code != 200) { xlog("L_ERR", "API error $var:code $var:reason\n"); $sht(sp=>$var:did)=0; return; }

  json_get_field($var:resp, "special_did", "$var:is_special");
  if ($var:is_special == "true" || $var:is_special == 1) { setflag(FLT_SPECIAL); $sht(sp=>$var:did)=1; append_hf("X-Special-DID: true\r\n"); }
  else $sht(sp=>$var:did)=0;
}
```

#### Tips
- Keep the API on the same LAN/VPC for low latency.
- The cache (`htable sp`) protects you from temporary API hiccups.
- The `X-Special-DID` header is useful for tracing in sngrep/pcap and can be consumed by downstream SBC/AS/FS.
- If you route different trunks/contexts for specials, implement that in `VIP_ROUTE`.

"""AfyaPlus Service Platform HTTP entry point."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Request

from service import __version__
from service.auth import authenticate, require_roles
from service.config import get_settings
from service.models import LoginRequest, TokenResponse, TriageRequest, TriageResponse
from service.triage import assess_triage

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
)
log = logging.getLogger("afyaplus.api")

app = FastAPI(title="AfyaPlus Service Platform", version=__version__)


@app.middleware("http")
async def trace_requests(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    log.info(
        "trace_id=%s method=%s path=%s status=%s",
        trace_id,
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "afyaplus", "version": __version__}


@app.post("/token", response_model=TokenResponse, tags=["authentication"])
def issue_token(login: LoginRequest) -> TokenResponse:
    return authenticate(login)


@app.post("/triage", response_model=TriageResponse, tags=["clinical"])
def triage(
    body: TriageRequest,
    request: Request,
    user: Annotated[dict[str, str], Depends(require_roles("clinician"))],
) -> TriageResponse:
    urgency, guidance = assess_triage(body)
    return TriageResponse(
        patient_id=body.patient_id,
        urgency=urgency,
        guidance=guidance,
        assessed_by=user["sub"],
        trace_id=request.state.trace_id,
    )


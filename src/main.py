import os
from typing import Any, Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException, Depends
from starlette.responses import Response

from src.services.crypto_service import CryptoService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/crypto/available", response_model=Optional[list[str]])
def get_crypto_available(
    base_currency: str | None = None,
    quote_currency: str | None = None,
    crypto_service: CryptoService = Depends(CryptoService),
):
    try:
        return crypto_service.get_list_of_symbols(
            base_currency=base_currency, quote_currency=quote_currency
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}") from e


@app.get("/api/v1/crypto/available")
def get_crypto_history(
    symbol: str,
    timeframe: str,
    since: str | None = None,
    limit: int | None = None,
    crypto_service: CryptoService = Depends(CryptoService),
):
    try:
        return crypto_service.get_history_of_symbol(symbol, since, limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}") from e


def start():
    """Launched with `poetry run start` at root level"""
    if os.getenv("APP_ENV", "dev") == "dev":
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=int(os.getenv("APP_PORT", "8000")),
            reload=True,
        )
    else:
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=int(os.getenv("APP_PORT", "8000")),
            reload=False,
            workers=4,
        )

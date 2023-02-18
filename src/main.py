import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.crypto_service import CryptoService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/crypto/available", response_model=list[str] | list | dict[str, str])
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


@app.get(
    "/api/v1/crypto/history",
    response_model=list[dict[str, float]] | dict[str, str],
)
def get_crypto_history(
    background_tasks: BackgroundTasks,
    symbol: str,
    timeframe: str,
    limit: int | None = None,
    crypto_service: CryptoService = Depends(CryptoService),
):
    try:
        if timeframe in [
            "1min",
            "2min",
            "5min",
            "15min",
            "30min",
            "1hour",
        ] and not crypto_service.check_file_exists(symbol, timeframe):
            background_tasks.add_task(
                crypto_service.get_history_of_symbol, symbol, timeframe
            )
            return {
                "message": "Warning the timeframe and crypto you selected needs a long download time please retry in a few minutes."
            }
        df_to_send = crypto_service.get_history_of_symbol(symbol, timeframe)
        if limit is not None and limit > 0 and len(df_to_send) > limit:
            return df_to_send[-limit:]
        return df_to_send
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e}") from e


def start():
    """Launched with `poetry run start` at root level"""
    CryptoService().refresh_list_of_symbols()
    scheduler = BackgroundScheduler()
    scheduler.add_job(CryptoService().refresh_list_of_symbols, trigger="cron", day="*")
    scheduler.start()
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

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field

def get_window_start(dt: datetime, window_minutes: int = 15) -> datetime:
    """
    Funkcja pomocnicza zaokrąglająca czas w dół do najbliższego interwału.
    Przykład dla 15 min: 14:07 -> 14:00, 14:23 -> 14:15.
    """
    # Zaokrąglamy minuty w dół do najbliższej wielokrotności okna
    rounded_minutes = (dt.minute // window_minutes) * window_minutes
    return dt.replace(minute=rounded_minutes, second=0, microsecond=0)

class MLModelRouting(BaseModel):
    """
    Wspólny model reprezentujący dane modelu ML rozproszone na dwie bazy.
    Z tego kontraktu będą korzystać zarówno funkcje zapisu, jak i odczytu.
    """
    model_name: str = Field(..., description="Unikalna nazwa modelu, np. 'digit-recognizer-v1'")
    
    # -- DANE DO REDIS --
    ip_address: Optional[str] = Field(None, description="Adres IP z portem, z Redis (np. '127.0.0.1:8000')")
    
    # -- DANE DO POSTGRES (tabela `model_registry`) --
    health_status: str = Field("OK", description="Status zdrowia z Postgres ('OK', 'FAILED')")
    last_called_at: Optional[datetime] = Field(None, description="Czas ostatniego użycia z Postgres")

class ModelUsageMetric(BaseModel):
    """
    Model pomocniczy do logowania metryk do tabeli `model_usage_metrics` (Postgres).
    Automatycznie oblicza 'time_window_start' i 'time_window_end'.
    """
    model_name: str
    time_window_start: datetime
    time_window_end: datetime
    request_count: int = 1  # Ile requestów chcemy zalogować (np. 1 na każde wywołanie)

    @classmethod
    def create_for_now(cls, model_name: str, window_minutes: int = 15, request_count: int = 1):
        """
        Narzędzie (Factory Method) by automatycznie tworzyć obiekty dla obecnej chwili
        wpadające w poprawne 15-minutowe (lub inne) "wiaderko" czasowe.
        """
        now = datetime.now()
        start = get_window_start(now, window_minutes)
        end = start + timedelta(minutes=window_minutes)
        
        return cls(
            model_name=model_name,
            time_window_start=start,
            time_window_end=end,
            request_count=request_count
        )

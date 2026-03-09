from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field

def get_window_start(dt: datetime, window_minutes: int = 15) -> datetime:
    """
    Helper that floors a datetime down to the nearest interval boundary.
    Example for 15 min: 14:07 -> 14:00, 14:23 -> 14:15.
    """
    # Round minutes down to the nearest multiple of the window size
    rounded_minutes = (dt.minute // window_minutes) * window_minutes
    return dt.replace(minute=rounded_minutes, second=0, microsecond=0)


class MLModelRouting(BaseModel):
    """
    Shared model representing ML model data spread across two databases.
    Both write and read functions work against this same contract.
    """
    model_name: str = Field(..., description="Unique model name, e.g. 'digit-recognizer-v1'")
    
    # -- REDIS fields --
    ip_address: Optional[str] = Field(None, description="IP address with port, from Redis (e.g. '127.0.0.1:8000')")
    
    # -- POSTGRES fields (table `model_registry`) --
    health_status: str = Field("OK", description="Health status from Postgres ('OK', 'FAILED')")
    last_called_at: Optional[datetime] = Field(None, description="Timestamp of last usage from Postgres")
    created_at: Optional[datetime] = Field(None, description="Timestamp of first time usage in Postgres")

    def __str__(self):
        return f""" Model: {self.model_name} \n IP: {self.ip_address}
 Status: {self.health_status} \n Last Called At: {self.last_called_at}
 Created At: {self.created_at}"""
    

class ModelUsageMetric(BaseModel):
    """
    Helper model for logging metrics into the `model_usage_metrics` table (Postgres).
    Automatically computes 'time_window_start' and 'time_window_end'.
    """
    model_name: str
    time_window_start: datetime
    time_window_end: datetime
    request_count: int = 1  # how many requests to log at once (usually 1 per call)

    @classmethod
    def create_for_now(cls, model_name: str, window_minutes: int = 15, request_count: int = 1):
        """
        Factory method that creates an instance bucketed into the correct
        15-minute (or other) time window for the current moment.
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

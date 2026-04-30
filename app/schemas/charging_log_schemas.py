from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Create_charging_log(BaseModel):
    user_id: int
    hydrogen_station_id: int
    vehicle_id: int
    start_time: datetime
    end_time: datetime
    charged_amount: float
    waiting_time: int

class charging_log_schemas_Response(BaseModel):
    charging_log_id: int
    model_config: ConfigDict(from_attributes=True)


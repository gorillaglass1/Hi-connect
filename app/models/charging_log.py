from app.core.database import Base



    charged_amount = Column(Numeric(6, 2))
    charging_cost = Column(Numeric(10, 2))
    waiting_time = Column(Integer)
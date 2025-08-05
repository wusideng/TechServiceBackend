import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import delete
from sqlmodel import Session, select
from app.core.database import engine
from app.model.t_coupon import T_Coupon


def main(openid):
    with Session(engine) as session:
        delete_statement = delete(T_Coupon).where(T_Coupon.open_id == openid)
        result = session.exec(delete_statement)
        session.commit()


if __name__ == "__main__":
    openid = "oK9p06S43s67ui0VxR3-h3REu0VY"
    main(openid)

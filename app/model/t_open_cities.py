from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional


class T_Open_Cities(SQLModel, table=True):

    __tablename__ = "t_open_cities"

    id: Optional[int] = Field(default=None, primary_key=True)
    city: str
    city_order: int
    created_time: datetime = Field(default_factory=datetime.now)


# CREATE TABLE home_massage_dev.dbo.t_open_cities (
# 	id int IDENTITY(1,1) NOT NULL,
# 	city nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
# 	created_time datetime2 DEFAULT getdate() NOT NULL,
# 	city_order int NOT NULL,
# 	CONSTRAINT PK__t_open_c__3213E83F4C0144E4 PRIMARY KEY (id),
# 	CONSTRAINT UK_t_open_cities_city UNIQUE (city)
# );
# INSERT INTO home_massage_prod.dbo.t_open_cities (city, city_order) VALUES
# ('杭州市',1),
# ('重庆市',2),
# ('石家庄市',3),
# ('安康市',4),
# ('北京市',5),
# ('青岛市',6);

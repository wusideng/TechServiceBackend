from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class T_Tech_USER_Contract(SQLModel, table=True):
    __tablename__ = "t_tech_user_contracts"
    contracts_id: Optional[int] = Field(default=None, primary_key=True)
    tech_openid: str = Field(max_length=100)
    tech_name: str = Field(max_length=100)
    tech_sex: Optional[str] = Field(max_length=20)
    tech_card_id:Optional[str] = Field(max_length=20)
    phone: str = Field(max_length=18)
    dealer_name: Optional[str] = Field(max_length=50)
    dealer_phone: Optional[str] = Field(max_length=20)
    dealer_owner_name: Optional[str] = Field(max_length=50)
    dealer_owner_phone: Optional[str] = Field(max_length=20)
    dealer_owner_card_id: Optional[str] = Field(max_length=20)
    photo_front: Optional[str] = Field(max_length=255)     # 存储身份证照片的路径或URL
    photo_back: Optional[str] = Field(max_length=255, nullable=True)
    signature: Optional[str] = Field(max_length=255)  # 存储签字图片的路径或URL
    contract_file: str = Field(max_length=255)   # 存储签字后合约文件的路径或URL
    contract_type: str = Field(max_length=255)    # 合约状态：apply（已提交）、approved（已审核）、rejected（已拒绝）
    status: str = Field(default="pending", max_length=50)
    status_desc: str = Field(default="审核信息", max_length=255)
    created_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

    # IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_tech_user_contracts')
    # BEGIN
    #     CREATE TABLE [dbo].[t_tech_user_contracts](
    #         [contracts_id] INT IDENTITY(1,1) PRIMARY KEY,	
    #         [tech_openid] nvarchar(100)NOT NULL,
    #         [tech_name] NVARCHAR(100) NOT NULL,
    #         [tech_sex] NVARCHAR(20) NOT NULL,
    #         [phone] NVARCHAR(18) NOT NULL,
    #         [photo_front] NVARCHAR(255) NOT NULL,
    #         [photo_back] NVARCHAR(255) NOT NULL,
    #         [signature] NVARCHAR(255) NOT NULL,
    #         [contract_file] NVARCHAR(255) NOT NULL,
    #         [contract_type] NVARCHAR(255) NOT NULL,
    #         [status] NVARCHAR(50) NOT NULL DEFAULT 'pending',
    #         [created_time] DATETIME NOT NULL DEFAULT GETDATE()
    #     );
    #     EXEC sys.sp_addextendedproperty 'MS_Description', '技师合约表', 'SCHEMA', 'dbo', 'TABLE', 't_technician_contracts';
    # END
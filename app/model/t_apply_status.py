# 申请状态表
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Apply_Status(SQLModel, table=True):
    apply_id: Optional[int] = Field(default=None, primary_key=True)
    apply_type: str
    tech_id: str
    apply_status: str
    emergency_contact: Optional[str]
    apply_refuse_cause: Optional[str]
    work_phone: Optional[str]
    user_nickname: Optional[str]
    user_sex: Optional[str]
    user_age: Optional[int]
    user_city: Optional[str]
    user_desc: Optional[str]
    bank_card_id: Optional[str]
    bank_card_type: Optional[str]
    photo_work: Optional[str]
    photo_life_1: Optional[str]
    photo_life_2: Optional[str]
    photo_life_3: Optional[str]
    business_license: Optional[str]
    technician_certificate: Optional[str]
    health_certificate: Optional[str]
    createTime: datetime = Field(default_factory=datetime.now)
    updateTime: Optional[datetime]


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_apply_status')

# CREATE TABLE [dbo].[t_apply_status](
#     [apply_id] int IDENTITY(1,1) PRIMARY KEY,
#     [apply_type] nvarchar(20) NOT NULL,
#     [tech_id] nvarchar(100) NOT NULL,
#     [apply_status] nvarchar(20) NOT NULL,
#     [apply_refuse_cause] nvarchar(200) NULL,
#     [work_phone] nvarchar(20) NULL,
#     [user_nickname] nvarchar(20) NULL,
#     [user_sex] nvarchar(20) NULL,
#     [user_age] int NULL,
#     [user_city] nvarchar(20) NULL,
#     [photo_work] nvarchar(200) NULL,
#     [photo_life_1] nvarchar(200) NULL,
#     [photo_life_2] nvarchar(200) NULL,
#     [photo_life_3] nvarchar(200) NULL,
#     [business_license] nvarchar(200) NULL,
#     [technician_certificate] nvarchar(200) NULL,
#     [health_certificate] nvarchar(200) NULL,
#     [createTime] datetime NOT NULL,
#     [updateTime] datetime NULL,	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','审批申请id(主键)','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','apply_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师上线，照片审批（techJoin，techWorkPhoto，techLifePhoto）','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','apply_type';
# EXEC sys.sp_addextendedproperty 'MS_Description','上线申请，照片审核申请(提款申请，物料包购买??)','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','tech_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','申请，批准，驳回','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','apply_status';
# EXEC sys.sp_addextendedproperty 'MS_Description','驳回原因','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','apply_refuse_cause';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师申请上线，审批通过更新到技师表，可用于临时查看','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','work_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师申请上线，审批通过更新到技师表，可用于临时查看','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','user_nickname';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师申请上线，审批通过更新到技师表，可用于临时查看','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','user_sex';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师申请上线，审批通过更新到技师表，可用于临时查看','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','user_age';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师申请上线，审批通过更新到技师表，可用于临时查看','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','user_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','照片审批，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','photo_work';
# EXEC sys.sp_addextendedproperty 'MS_Description','照片审批，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','photo_life_1';
# EXEC sys.sp_addextendedproperty 'MS_Description','照片审批，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','photo_life_2';
# EXEC sys.sp_addextendedproperty 'MS_Description','照片审批，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','photo_life_3';
# EXEC sys.sp_addextendedproperty 'MS_Description','商户执照，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','business_license';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师证，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','technician_certificate';
# EXEC sys.sp_addextendedproperty 'MS_Description','健康证，审批通过更新到技师表','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','health_certificate';
# EXEC sys.sp_addextendedproperty 'MS_Description','申请时间','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','createTime';
# EXEC sys.sp_addextendedproperty 'MS_Description','更新时间（审批时间）','SCHEMA','dbo','TABLE','t_apply_status','COLUMN','updateTime';

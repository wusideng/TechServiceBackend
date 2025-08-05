from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class T_Sms_Code(SQLModel, table=True):
    """短信验证码"""

    __tablename__ = "t_sms_code"

    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(max_length=11, description="手机号码", index=True)
    code: str = Field(max_length=6, description="验证码")
    create_time: datetime = Field(default_factory=datetime.now, description="发送时间")
    expire_time: datetime = Field(description="过期时间")
    is_used: bool = Field(default=False, description="是否已使用:0-否/1-是")


# -- 创建短信验证码表
# CREATE TABLE t_sms_code (
#     id INT IDENTITY(1,1),
#     phone NVARCHAR(11) NOT NULL,
#     code NVARCHAR(6) NOT NULL,
#     created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
#     expires_at DATETIME2 NOT NULL,
#     is_used BIT NOT NULL DEFAULT 0,
#     last_send_time DATETIME2 NULL,
#     CONSTRAINT t_sms_code_pk PRIMARY KEY (id)
# );

# -- 添加注释
# EXEC sp_addextendedproperty 'MS_Description',
# '短信验证码表',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code';

# EXEC sp_addextendedproperty 'MS_Description',
# '主键ID',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'id';

# EXEC sp_addextendedproperty 'MS_Description',
# '手机号码',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'phone';

# EXEC sp_addextendedproperty 'MS_Description',
# '验证码',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'code';

# EXEC sp_addextendedproperty 'MS_Description',
# '创建时间',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'created_at';

# EXEC sp_addextendedproperty 'MS_Description',
# '过期时间',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'expires_at';

# EXEC sp_addextendedproperty 'MS_Description',
# '是否已使用(0-否/1-是)',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'is_used';

# EXEC sp_addextendedproperty 'MS_Description',
# '最后发送时间',
# 'SCHEMA',
# 'dbo',
# 'TABLE',
# 't_sms_code',
# 'COLUMN',
# 'last_send_time';

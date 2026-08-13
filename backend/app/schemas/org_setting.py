from pydantic import BaseModel


class OrgSettingUpsert(BaseModel):
    key: str
    value: str


class OrgSettingRead(BaseModel):
    key: str
    value: str

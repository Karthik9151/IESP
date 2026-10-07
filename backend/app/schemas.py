from __future__ import annotations
import re
from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator
class Strict(BaseModel): model_config=ConfigDict(extra='forbid')
class RegisterRequest(Strict):
    email:str=Field(min_length=5,max_length=320); password:str=Field(min_length=10,max_length=128)
    @field_validator('email')
    @classmethod
    def valid_email(cls,v):
        v=v.strip().lower()
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',v): raise ValueError('Valid email required')
        return v
class LoginRequest(RegisterRequest): pass
class UserResponse(Strict): id:int; email:str
class WorkspaceResponse(Strict): id:int; name:str; role:str
class SessionResponse(Strict): user:UserResponse; workspace:WorkspaceResponse
class AttachmentRequest(Strict):
    filename:str=Field(min_length=1,max_length=512); content_type:str=Field(min_length=1,max_length=256); size_bytes:int|None=Field(default=None,ge=0,le=10*1024*1024); disposition:Literal['inline','attachment']|None=None
class EmailRequest(Strict):
    message_id:str=Field(min_length=1,max_length=512); sender:str=Field(min_length=3,max_length=1024); recipients:list[str]=Field(min_length=1,max_length=50); subject:str=Field(default='',max_length=1000); text_body:str=Field(default='',max_length=500000); html_body:str=Field(default='',max_length=500000); headers:dict[str,str]=Field(default_factory=dict,max_length=100); attachments:list[AttachmentRequest]=Field(default_factory=list,max_length=25); received_timestamp:datetime|None=None
    @field_validator('message_id','sender','subject','text_body','html_body',mode='before')
    @classmethod
    def safe(cls,v):
        if not isinstance(v,str) or any(c in v for c in ('\x00','\r')): raise ValueError('Invalid text value')
        return v
    @field_validator('headers')
    @classmethod
    def headers_safe(cls,v):
        for k,x in v.items():
            if not re.fullmatch(r"[A-Za-z0-9!#$%&'*+._^|~-]+",k) or any(c in x for c in ('\x00','\r','\n')) or len(x)>8192: raise ValueError('Invalid header')
        return v
class SecurityReason(Strict): code:str; severity:str; category:str; message:str; evidence:dict={}
class SecurityResponse(Strict): classification:str; risk_score:float=Field(ge=0,le=100); model_score:float|None=None; model_score_kind:Literal['decision_margin','unavailable']; reasons:list[SecurityReason]=[]
class PriorityResponse(Strict): label:str; proxy_label:bool=True; score_by_class:dict[str,float]={}
class ModelInfoResponse(Strict): phishing:str; priority:str|None=None; model_version:str; policy_version:str
class AnalysisResponse(Strict): message_id:str; request_id:str; security:SecurityResponse; priority:PriorityResponse|None=None; model_info:ModelInfoResponse
class RecentAnalysisItem(Strict): message_id:str; request_id:str; classification:str; risk_score:float; priority:str|None; created_at:datetime
class PaginatedAnalysisResponse(Strict): items:list[RecentAnalysisItem]; total:int
class StatsResponse(Strict): total:int; phishing:int; suspicious:int; non_phishing:int; review_required:int
class HealthResponse(Strict): status:Literal['ok']
class ReadyResponse(Strict): status:Literal['ready','not_ready']; blockers:list[str]=[]
class ErrorResponse(Strict): code:str; message:str; request_id:str|None=None

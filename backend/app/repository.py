from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from src.domain.models import AnalysisResult

class AnalysisRepository(Protocol):
    def save(self,result,user_id:int,workspace_id:int)->None: ...
    def get(self,workspace_id:int,message_id:str)->dict|None: ...
    def recent(self,workspace_id:int,limit:int=50)->list[dict]: ...
    def stats(self,workspace_id:int)->dict[str,int]: ...
    def register_user(self,email:str,password_hash:str)->dict: ...
    def get_user_by_email(self,email:str)->dict|None: ...
    def create_session(self,token_hash:str,user_id:int,workspace_id:int,expires_at:datetime)->None: ...
    def get_session(self,token_hash:str)->dict|None: ...
    def delete_session(self,token_hash:str)->None: ...
    def ping(self)->bool: ...

SCHEMA="""
CREATE TABLE IF NOT EXISTS app_users(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workspaces(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workspace_members(workspace_id INTEGER NOT NULL,user_id INTEGER NOT NULL,role TEXT NOT NULL,PRIMARY KEY(workspace_id,user_id));
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,workspace_id INTEGER NOT NULL,expires_at TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS analysis_results(id INTEGER PRIMARY KEY AUTOINCREMENT,message_id TEXT NOT NULL,request_id TEXT NOT NULL,user_id INTEGER NOT NULL,workspace_id INTEGER NOT NULL,sender_email TEXT NOT NULL,subject TEXT NOT NULL,classification TEXT NOT NULL,reasons_json TEXT NOT NULL,priority_label TEXT,risk_score REAL NOT NULL,created_at TEXT NOT NULL,model_version TEXT NOT NULL,policy_version TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_analysis_workspace_created ON analysis_results(workspace_id,created_at DESC);
"""

def _risk(classification:str,reasons:list[dict])->float:
    base={'PHISHING':90.0,'SUSPICIOUS':65.0,'REVIEW REQUIRED':45.0,'NON-PHISHING':10.0}.get(classification,50.0)
    severity={'CRITICAL':10,'HIGH':7,'MEDIUM':4,'LOW':2,'INFO':0}
    bonus=sum(severity.get(str(x.get('severity')),0) for x in reasons)
    return min(100.0,base+min(10.0,bonus))

class SQLiteAnalysisRepository:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._init_db()
    def _connect(self):
        c=sqlite3.connect(self.path,timeout=5); c.row_factory=sqlite3.Row; return c
    def _init_db(self):
        with self._connect() as c: c.executescript(SCHEMA)
    def ping(self):
        try:
            with self._connect() as c:c.execute('SELECT 1')
            return True
        except Exception:return False
    def register_user(self,email,password_hash):
        now=datetime.now(timezone.utc).isoformat()
        with self._connect() as c:
            if c.execute('SELECT 1 FROM app_users WHERE email=?',(email,)).fetchone(): raise ValueError('EMAIL_EXISTS')
            uid=int(c.execute('INSERT INTO app_users(email,password_hash,created_at) VALUES(?,?,?) RETURNING id',(email,password_hash,now)).fetchone()[0])
            name=email+' workspace'; wid=int(c.execute('INSERT INTO workspaces(name,created_at) VALUES(?,?) RETURNING id',(name,now)).fetchone()[0])
            c.execute('INSERT INTO workspace_members VALUES(?,?,?)',(wid,uid,'owner'))
        return {'id':uid,'email':email,'workspace_id':wid,'workspace_name':name,'role':'owner'}
    def get_user_by_email(self,email):
        with self._connect() as c:
            r=c.execute('SELECT u.id,u.email,u.password_hash,w.id workspace_id,w.name workspace_name,wm.role FROM app_users u JOIN workspace_members wm ON wm.user_id=u.id JOIN workspaces w ON w.id=wm.workspace_id WHERE u.email=? LIMIT 1',(email,)).fetchone()
        return dict(r) if r else None
    def create_session(self,token_hash,user_id,workspace_id,expires_at):
        with self._connect() as c:c.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(token_hash,user_id,workspace_id,expires_at.isoformat(),datetime.now(timezone.utc).isoformat()))
    def get_session(self,token_hash):
        with self._connect() as c:r=c.execute('SELECT s.user_id,s.workspace_id,s.expires_at,u.email,wm.role FROM sessions s JOIN app_users u ON u.id=s.user_id JOIN workspace_members wm ON wm.workspace_id=s.workspace_id AND wm.user_id=s.user_id WHERE s.token_hash=?',(token_hash,)).fetchone()
        if not r:return None
        if datetime.fromisoformat(r['expires_at'])<=datetime.now(timezone.utc):self.delete_session(token_hash);return None
        return dict(r)
    def delete_session(self,token_hash):
        with self._connect() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(token_hash,))
    def save(self,result,user_id,workspace_id):
        reasons=[{'code':r.code,'severity':r.severity.value,'category':r.category,'message':r.message,'evidence':r.evidence} for r in result.security.reasons]
        with self._connect() as c:c.execute('INSERT INTO analysis_results(message_id,request_id,user_id,workspace_id,sender_email,subject,classification,reasons_json,priority_label,risk_score,created_at,model_version,policy_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(result.message_id,result.request_id or '',user_id,workspace_id,'','',result.security.classification.value,json.dumps(reasons,sort_keys=True),result.priority.label.value if result.priority else None,_risk(result.security.classification.value,reasons),datetime.now(timezone.utc).isoformat(),'IESP-configured-model','policy-v1'))
    def get(self,workspace_id,message_id):
        with self._connect() as c:r=c.execute('SELECT message_id,request_id,sender_email,subject,classification,reasons_json,priority_label,risk_score,created_at,model_version,policy_version FROM analysis_results WHERE workspace_id=? AND message_id=? ORDER BY id DESC LIMIT 1',(workspace_id,message_id)).fetchone()
        return self._row(r) if r else None
    def recent(self,workspace_id,limit=50):
        with self._connect() as c:rows=c.execute('SELECT message_id,request_id,sender_email,subject,classification,reasons_json,priority_label,risk_score,created_at,model_version,policy_version FROM analysis_results WHERE workspace_id=? ORDER BY id DESC LIMIT ?',(workspace_id,max(1,min(int(limit),100)))).fetchall()
        return [self._row(r) for r in rows]
    def stats(self,workspace_id):
        with self._connect() as c:
            total=c.execute('SELECT COUNT(*) FROM analysis_results WHERE workspace_id=?',(workspace_id,)).fetchone()[0]; rows=c.execute('SELECT classification,COUNT(*) count FROM analysis_results WHERE workspace_id=? GROUP BY classification',(workspace_id,)).fetchall()
        d={r['classification']:int(r['count']) for r in rows};return {'total':int(total),'phishing':d.get('PHISHING',0),'suspicious':d.get('SUSPICIOUS',0),'non_phishing':d.get('NON-PHISHING',0),'review_required':d.get('REVIEW REQUIRED',0)}
    @staticmethod
    def _row(r):
        return {'message_id':r['message_id'],'request_id':r['request_id'],'sender':r['sender_email'],'subject':r['subject'],'classification':r['classification'],'reasons':json.loads(r['reasons_json']),'priority':r['priority_label'],'risk_score':r['risk_score'],'created_at':r['created_at'],'model_version':r['model_version'],'policy_version':r['policy_version']}

def build_repository(settings):
    if settings.database_url.startswith(('postgres://','postgresql://')):
        return PostgresAnalysisRepository(settings.database_url)
    return SQLiteAnalysisRepository(settings.database_path)

class PostgresAnalysisRepository:
    def __init__(self,url):
        import psycopg
        self.psycopg=psycopg; self.url=url.replace('postgres://','postgresql://',1); self._init_db()
    def _connect(self): return self.psycopg.connect(self.url)
    def _init_db(self):
        with self._connect() as c:
            c.execute(SCHEMA.replace('INTEGER PRIMARY KEY AUTOINCREMENT','BIGSERIAL PRIMARY KEY').replace('INTEGER NOT NULL','BIGINT NOT NULL').replace('AUTOINCREMENT',''))
    def ping(self):
        try:
            with self._connect() as c:c.execute('SELECT 1')
            return True
        except Exception:return False


class PostgresAnalysisRepository:
    def __init__(self,url):
        import psycopg
        self.psycopg=psycopg; self.url=url.replace('postgres://','postgresql://',1); self._init_db()
    def _connect(self): return self.psycopg.connect(self.url)
    def _init_db(self):
        schema=SCHEMA.replace('INTEGER PRIMARY KEY AUTOINCREMENT','BIGSERIAL PRIMARY KEY').replace('INTEGER NOT NULL','BIGINT NOT NULL')
        with self._connect() as c:
            for stmt in schema.split(';'):
                if stmt.strip(): c.execute(stmt)
    def ping(self):
        try:
            with self._connect() as c: c.execute('SELECT 1')
            return True
        except Exception:return False
    def register_user(self,email,password_hash):
        now=datetime.now(timezone.utc).isoformat()
        with self._connect() as c:
            if c.execute('SELECT 1 FROM app_users WHERE email=%s',(email,)).fetchone(): raise ValueError('EMAIL_EXISTS')
            uid=c.execute('INSERT INTO app_users(email,password_hash,created_at) VALUES(%s,%s,%s) RETURNING id',(email,password_hash,now)).fetchone()[0]
            name=email+' workspace'; wid=c.execute('INSERT INTO workspaces(name,created_at) VALUES(%s,%s) RETURNING id',(name,now)).fetchone()[0]
            c.execute('INSERT INTO workspace_members VALUES(%s,%s,%s)',(wid,uid,'owner'))
        return {'id':uid,'email':email,'workspace_id':wid,'workspace_name':name,'role':'owner'}
    def get_user_by_email(self,email):
        with self._connect() as c:r=c.execute('SELECT u.id,u.email,u.password_hash,w.id workspace_id,w.name workspace_name,wm.role FROM app_users u JOIN workspace_members wm ON wm.user_id=u.id JOIN workspaces w ON w.id=wm.workspace_id WHERE u.email=%s LIMIT 1',(email,)).fetchone()
        return None if not r else {'id':r[0],'email':r[1],'password_hash':r[2],'workspace_id':r[3],'workspace_name':r[4],'role':r[5]}
    def create_session(self,token_hash,user_id,workspace_id,expires_at):
        with self._connect() as c:c.execute('INSERT INTO sessions VALUES(%s,%s,%s,%s,%s)',(token_hash,user_id,workspace_id,expires_at.isoformat(),datetime.now(timezone.utc).isoformat()))
    def get_session(self,token_hash):
        with self._connect() as c:r=c.execute('SELECT s.user_id,s.workspace_id,s.expires_at,u.email,wm.role FROM sessions s JOIN app_users u ON u.id=s.user_id JOIN workspace_members wm ON wm.workspace_id=s.workspace_id AND wm.user_id=s.user_id WHERE s.token_hash=%s',(token_hash,)).fetchone()
        if not r:return None
        if datetime.fromisoformat(r[2])<=datetime.now(timezone.utc):self.delete_session(token_hash);return None
        return {'user_id':r[0],'workspace_id':r[1],'expires_at':r[2],'email':r[3],'role':r[4]}
    def delete_session(self,token_hash):
        with self._connect() as c:c.execute('DELETE FROM sessions WHERE token_hash=%s',(token_hash,))
    def save(self,result,user_id,workspace_id):
        reasons=[{'code':r.code,'severity':r.severity.value,'category':r.category,'message':r.message,'evidence':r.evidence} for r in result.security.reasons]
        with self._connect() as c:c.execute('INSERT INTO analysis_results(message_id,request_id,user_id,workspace_id,sender_email,subject,classification,reasons_json,priority_label,risk_score,created_at,model_version,policy_version) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(result.message_id,result.request_id or '',user_id,workspace_id,'','',result.security.classification.value,json.dumps(reasons,sort_keys=True),result.priority.label.value if result.priority else None,_risk(result.security.classification.value,reasons),datetime.now(timezone.utc).isoformat(),'IESP-configured-model','policy-v1'))
    def get(self,workspace_id,message_id):
        with self._connect() as c:r=c.execute('SELECT message_id,request_id,sender_email,subject,classification,reasons_json,priority_label,risk_score,created_at,model_version,policy_version FROM analysis_results WHERE workspace_id=%s AND message_id=%s ORDER BY id DESC LIMIT 1',(workspace_id,message_id)).fetchone()
        return self._row(r) if r else None
    def recent(self,workspace_id,limit=50):
        with self._connect() as c:rows=c.execute('SELECT message_id,request_id,sender_email,subject,classification,reasons_json,priority_label,risk_score,created_at,model_version,policy_version FROM analysis_results WHERE workspace_id=%s ORDER BY id DESC LIMIT %s',(workspace_id,max(1,min(int(limit),100)))).fetchall()
        return [self._row(r) for r in rows]
    def stats(self,workspace_id):
        with self._connect() as c:
            total=c.execute('SELECT COUNT(*) FROM analysis_results WHERE workspace_id=%s',(workspace_id,)).fetchone()[0]; rows=c.execute('SELECT classification,COUNT(*) FROM analysis_results WHERE workspace_id=%s GROUP BY classification',(workspace_id,)).fetchall()
        d={r[0]:int(r[1]) for r in rows};return {'total':int(total),'phishing':d.get('PHISHING',0),'suspicious':d.get('SUSPICIOUS',0),'non_phishing':d.get('NON-PHISHING',0),'review_required':d.get('REVIEW REQUIRED',0)}
    @staticmethod
    def _row(r): return {'message_id':r[0],'request_id':r[1],'sender':r[2],'subject':r[3],'classification':r[4],'reasons':json.loads(r[5]),'priority':r[6],'risk_score':r[7],'created_at':r[8],'model_version':r[9],'policy_version':r[10]}


def build_repository(settings):
    return PostgresAnalysisRepository(settings.database_url) if settings.database_url.startswith(('postgres://','postgresql://')) else SQLiteAnalysisRepository(settings.database_path)

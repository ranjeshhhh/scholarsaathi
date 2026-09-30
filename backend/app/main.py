"""ScholarSaathi prototype API. Demo records never imply an active official scheme."""
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./scholarsaathi.db')
SECRET_KEY=os.getenv('JWT_SECRET_KEY','local-demo-key-change-before-deployment')
ALGORITHM='HS256'
engine=create_engine(DATABASE_URL,connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {},pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True);email:Mapped[str]=mapped_column(String(255),unique=True,index=True);password_hash:Mapped[str]=mapped_column(String(255));role:Mapped[str]=mapped_column(String(20),default='student');name:Mapped[str]=mapped_column(String(160));created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Profile(Base):
    __tablename__='student_profiles'
    id:Mapped[int]=mapped_column(primary_key=True);user_id:Mapped[int]=mapped_column(ForeignKey('users.id'),unique=True,index=True);state:Mapped[Optional[str]]=mapped_column(String(100),nullable=True);course:Mapped[Optional[str]]=mapped_column(String(160),nullable=True);annual_income:Mapped[Optional[int]]=mapped_column(Integer,nullable=True);category:Mapped[Optional[str]]=mapped_column(String(80),nullable=True);academic_score:Mapped[Optional[float]]=mapped_column(Float,nullable=True);income_certificate:Mapped[bool]=mapped_column(Boolean,default=False)
class Provider(Base):
    __tablename__='providers'
    id:Mapped[int]=mapped_column(primary_key=True);name:Mapped[str]=mapped_column(String(200));official_website:Mapped[str]=mapped_column(String(500));verification_status:Mapped[str]=mapped_column(String(40),default='unverified')
class Opportunity(Base):
    __tablename__='scholarships'
    id:Mapped[int]=mapped_column(primary_key=True);title:Mapped[str]=mapped_column(String(250),index=True);provider_id:Mapped[Optional[int]]=mapped_column(ForeignKey('providers.id'),nullable=True);provider_name:Mapped[str]=mapped_column(String(200));description:Mapped[str]=mapped_column(Text);kind:Mapped[str]=mapped_column(String(30),default='Scholarship');education_level:Mapped[str]=mapped_column(String(120),default='All levels');income_limit:Mapped[Optional[int]]=mapped_column(Integer,nullable=True);state_eligibility:Mapped[str]=mapped_column(String(160),default='All states');application_start:Mapped[Optional[date]]=mapped_column(Date,nullable=True);deadline:Mapped[Optional[date]]=mapped_column(Date,nullable=True);award_amount:Mapped[str]=mapped_column(String(120),default='See official guidelines');required_documents:Mapped[str]=mapped_column(Text,default='[]');application_url:Mapped[str]=mapped_column(String(500));source_url:Mapped[str]=mapped_column(String(500));last_verified:Mapped[Optional[date]]=mapped_column(Date,nullable=True);verified:Mapped[bool]=mapped_column(Boolean,default=False);demo:Mapped[bool]=mapped_column(Boolean,default=True);active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Application(Base):
    __tablename__='applications'
    id:Mapped[int]=mapped_column(primary_key=True);user_id:Mapped[int]=mapped_column(ForeignKey('users.id'),index=True);opportunity_id:Mapped[int]=mapped_column(ForeignKey('scholarships.id'));status:Mapped[str]=mapped_column(String(40),default='Preparing');reference:Mapped[str]=mapped_column(String(120),default='');created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Saved(Base):
    __tablename__='saved_scholarships'
    id:Mapped[int]=mapped_column(primary_key=True);user_id:Mapped[int]=mapped_column(ForeignKey('users.id'),index=True);opportunity_id:Mapped[int]=mapped_column(ForeignKey('scholarships.id'))
class Reminder(Base):
    __tablename__='reminders'
    id:Mapped[int]=mapped_column(primary_key=True);user_id:Mapped[int]=mapped_column(ForeignKey('users.id'),index=True);opportunity_id:Mapped[int]=mapped_column(ForeignKey('scholarships.id'));remind_on:Mapped[date]=mapped_column(Date);created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine)
def db():
    session=SessionLocal()
    try: yield session
    finally: session.close()
password_hash=PasswordHash.recommended();oauth=OAuth2PasswordBearer(tokenUrl='/auth/login')
def token_for(user:User): return jwt.encode({'sub':str(user.id),'role':user.role,'exp':datetime.now(timezone.utc)+timedelta(hours=12)},SECRET_KEY,algorithm=ALGORITHM)
def current_user(token:str=Depends(oauth),session:Session=Depends(db)):
    try: uid=int(jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])['sub'])
    except (JWTError,KeyError,ValueError): raise HTTPException(401,'Invalid or expired session')
    user=session.get(User,uid)
    if not user: raise HTTPException(401,'Account not found')
    return user
def admin(user:User=Depends(current_user)):
    if user.role!='admin': raise HTTPException(403,'Administrator access required')
    return user
class Register(BaseModel): name:str=Field(min_length=2,max_length=160);email:EmailStr;password:str=Field(min_length=10,max_length=128)
class Login(BaseModel): email:EmailStr;password:str
class ProfileInput(BaseModel): state:Optional[str]=None;course:Optional[str]=None;annual_income:Optional[int]=Field(default=None,ge=0);category:Optional[str]=None;academic_score:Optional[float]=Field(default=None,ge=0,le=100);income_certificate:bool=False
class OpportunityInput(BaseModel): title:str;provider_name:str;description:str;kind:str='Scholarship';education_level:str='All levels';income_limit:Optional[int]=None;state_eligibility:str='All states';deadline:Optional[date]=None;application_start:Optional[date]=None;award_amount:str='See official guidelines';required_documents:list[str]=[];application_url:str;source_url:str;verified:bool=False;demo:bool=True;last_verified:Optional[date]=None
class ApplyInput(BaseModel): opportunity_id:int;reference:str=''
class StatusInput(BaseModel): status:str;reference:str=''
class ReminderInput(BaseModel):opportunity_id:int;remind_on:date
class SaveInput(BaseModel):opportunity_id:int
class ChatInput(BaseModel):message:str=Field(min_length=1,max_length=1200)
def opportunity_json(o:Opportunity):
    expired=bool(o.deadline and o.deadline<date.today())
    return {'id':o.id,'title':o.title,'provider':o.provider_name,'description':o.description,'kind':o.kind,'education_level':o.education_level,'income_limit':o.income_limit,'state_eligibility':o.state_eligibility,'deadline':o.deadline,'application_start':o.application_start,'award_amount':o.award_amount,'required_documents':__import__('json').loads(o.required_documents),'application_url':o.application_url,'source_url':o.source_url,'last_verified':o.last_verified,'verified':o.verified,'demo':o.demo,'status':'Closed' if expired else ('Active' if o.verified and not o.demo and o.active else 'Verification Required'),'expired':expired}
app=FastAPI(title='ScholarSaathi API',version='1.0.0',description='Scholarship discovery API. Seed data is explicitly demo-only.')
origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(',')
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Authorization','Content-Type'])
@app.on_event('startup')
def seed():
    with SessionLocal() as s:
        if s.scalar(select(Opportunity.id).limit(1)):return
        for title,provider,source,kind in [('Post-Matric Scholarship for ST Students','Ministry of Tribal Affairs · Demo','https://tribal.nic.in/','Scholarship'),('National Fellowship for Higher Education of ST Students','Ministry of Tribal Affairs · Demo','https://tribal.nic.in/','Fellowship'),('Top Class Education Scheme for ST Students','Ministry of Tribal Affairs · Demo','https://tribal.nic.in/','Scholarship'),('National Scholarship Portal — ST schemes','National Scholarship Portal · Demo','https://scholarships.gov.in/','Scholarship')]:
            s.add(Opportunity(title=title,provider_name=provider,description='Illustrative demo listing. Not verified as currently open. Check the official provider for current eligibility and deadlines.',kind=kind,education_level='See official notice',deadline=None,source_url=source,application_url=source,verified=False,demo=True,active=True,award_amount='See official guidelines'))
        s.commit()
@app.get('/health')
def health():return {'ok':True,'mode':'demo','message':'Demo opportunity records are not live scheme data.'}
@app.post('/auth/register')
def register(data:Register,s:Session=Depends(db)):
    if s.scalar(select(User).where(User.email==data.email.lower())):raise HTTPException(409,'Email is already registered')
    u=User(email=data.email.lower(),name=data.name,password_hash=password_hash.hash(data.password),role='student');s.add(u);s.flush();s.add(Profile(user_id=u.id));s.commit();return {'access_token':token_for(u),'token_type':'bearer','user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}}
@app.post('/auth/login')
def login(data:Login,s:Session=Depends(db)):
    u=s.scalar(select(User).where(User.email==data.email.lower()))
    if not u or not password_hash.verify(data.password,u.password_hash):raise HTTPException(401,'Email or password is incorrect')
    return {'access_token':token_for(u),'token_type':'bearer','user':{'id':u.id,'name':u.name,'email':u.email,'role':u.role}}
@app.get('/profile')
def get_profile(u:User=Depends(current_user),s:Session=Depends(db)):
    p=s.scalar(select(Profile).where(Profile.user_id==u.id));return {'name':u.name,'email':u.email,'state':p.state,'course':p.course,'annual_income':p.annual_income,'category':p.category,'academic_score':p.academic_score,'income_certificate':p.income_certificate}
@app.patch('/profile')
def patch_profile(data:ProfileInput,u:User=Depends(current_user),s:Session=Depends(db)):
    p=s.scalar(select(Profile).where(Profile.user_id==u.id))
    for k,v in data.model_dump().items():setattr(p,k,v)
    s.commit();return get_profile(u,s)
@app.get('/scholarships')
def list_opportunities(q:str='',kind:str='',state:str='',active_only:bool=True,limit:int=30,offset:int=0,s:Session=Depends(db)):
    limit=min(max(limit,1),100);stmt=select(Opportunity).where(Opportunity.active.is_(True))
    if q:stmt=stmt.where(Opportunity.title.ilike(f'%{q}%')|Opportunity.provider_name.ilike(f'%{q}%')|Opportunity.education_level.ilike(f'%{q}%'))
    if kind:stmt=stmt.where(Opportunity.kind==kind)
    if state:stmt=stmt.where((Opportunity.state_eligibility=='All states')|(Opportunity.state_eligibility.ilike(f'%{state}%')))
    items=s.scalars(stmt.order_by(Opportunity.deadline.asc().nullslast(),Opportunity.created_at.desc()).offset(offset).limit(limit)).all()
    if active_only:items=[o for o in items if not o.deadline or o.deadline>=date.today()]
    return {'items':[opportunity_json(o) for o in items],'limit':limit,'offset':offset}
@app.get('/scholarships/{opportunity_id}')
def detail(opportunity_id:int,s:Session=Depends(db)):
    o=s.get(Opportunity,opportunity_id)
    if not o:raise HTTPException(404,'Opportunity not found')
    return opportunity_json(o)
@app.get('/fellowships')
def fellowships(s:Session=Depends(db)):return {'items':[opportunity_json(o) for o in s.scalars(select(Opportunity).where(Opportunity.kind=='Fellowship',Opportunity.active.is_(True))).all()]}
@app.post('/eligibility/check')
def recommendations(u:User=Depends(current_user),s:Session=Depends(db)):
    p=s.scalar(select(Profile).where(Profile.user_id==u.id));result=[]
    for o in s.scalars(select(Opportunity).where(Opportunity.active.is_(True))).all():
        reasons=[];missing=[];score=0
        if o.demo or not o.verified:missing.append('Opportunity is not verified; confirm all criteria at the source')
        if p.category and 'tribe' in p.category.lower():score+=30;reasons.append('Your profile indicates Scheduled Tribe category')
        if p.course and o.education_level!='All levels':score+=15;reasons.append('Course information is available for comparison')
        else:missing.append('Add your current course and check the official education-level requirement')
        if p.annual_income is not None and o.income_limit is not None:
            if p.annual_income<=o.income_limit:score+=30;reasons.append('Income is within the listed limit')
            else:missing.append('Income is above the listed limit')
        else:missing.append('Income limit is not verified or profile income is missing')
        result.append({'opportunity':opportunity_json(o),'score':min(score,75),'reasons':reasons,'missing_requirements':missing,'recommendation':'Needs review' if missing else 'Possible match'})
    return {'items':result}
@app.get('/recommendations')
def get_recommendations(u:User=Depends(current_user),s:Session=Depends(db)):return recommendations(u,s)
@app.post('/applications')
def create_application(data:ApplyInput,u:User=Depends(current_user),s:Session=Depends(db)):
    o=s.get(Opportunity,data.opportunity_id)
    if not o:raise HTTPException(404,'Opportunity not found')
    if o.deadline and o.deadline<date.today():raise HTTPException(409,'Application deadline has passed')
    a=Application(user_id=u.id,opportunity_id=o.id,reference=data.reference);s.add(a);s.commit();return {'id':a.id,'opportunity':opportunity_json(o),'status':a.status,'reference':a.reference}
@app.get('/applications')
def get_applications(u:User=Depends(current_user),s:Session=Depends(db)):
    return [{'id':a.id,'opportunity':opportunity_json(s.get(Opportunity,a.opportunity_id)),'status':a.status,'reference':a.reference,'created_at':a.created_at} for a in s.scalars(select(Application).where(Application.user_id==u.id)).all()]
@app.patch('/applications/{application_id}')
def update_application(application_id:int,data:StatusInput,u:User=Depends(current_user),s:Session=Depends(db)):
    a=s.get(Application,application_id)
    if not a or a.user_id!=u.id:raise HTTPException(404,'Application not found')
    if data.status not in ['Preparing','Submitted','Under review','Needs attention','Decision received']:raise HTTPException(422,'Unknown application status')
    a.status=data.status;a.reference=data.reference;s.commit();return {'id':a.id,'status':a.status,'reference':a.reference}
@app.post('/saved-scholarships')
def save_opportunity(data:SaveInput,u:User=Depends(current_user),s:Session=Depends(db)):
    if not s.get(Opportunity,data.opportunity_id):raise HTTPException(404,'Opportunity not found')
    if not s.scalar(select(Saved).where(Saved.user_id==u.id,Saved.opportunity_id==data.opportunity_id)):s.add(Saved(user_id=u.id,opportunity_id=data.opportunity_id));s.commit()
    return {'saved':True,'opportunity_id':data.opportunity_id}
@app.delete('/saved-scholarships/{opportunity_id}')
def unsave(opportunity_id:int,u:User=Depends(current_user),s:Session=Depends(db)):
    saved=s.scalar(select(Saved).where(Saved.user_id==u.id,Saved.opportunity_id==opportunity_id))
    if saved:s.delete(saved);s.commit()
    return {'saved':False}
@app.post('/reminders')
def reminder(data:ReminderInput,u:User=Depends(current_user),s:Session=Depends(db)):
    if not s.get(Opportunity,data.opportunity_id):raise HTTPException(404,'Opportunity not found')
    if data.remind_on<date.today():raise HTTPException(422,'Reminder date must be today or later')
    r=Reminder(user_id=u.id,opportunity_id=data.opportunity_id,remind_on=data.remind_on);s.add(r);s.commit();return {'id':r.id,'opportunity_id':r.opportunity_id,'remind_on':r.remind_on,'delivery':'Stored in app; outbound email/SMS requires provider configuration'}
@app.get('/notifications')
def notifications(u:User=Depends(current_user),s:Session=Depends(db)):
    return [{'id':r.id,'type':'reminder','message':'Reminder set for opportunity deadline','remind_on':r.remind_on,'opportunity':opportunity_json(s.get(Opportunity,r.opportunity_id))} for r in s.scalars(select(Reminder).where(Reminder.user_id==u.id)).all()]
@app.post('/ai/chat')
def chat(data:ChatInput,u:User=Depends(current_user),s:Session=Depends(db)):
    matches=s.scalars(select(Opportunity).where(Opportunity.title.ilike(f'%{data.message[:80]}%'))).all()
    note='I can answer only from this app’s current catalogue. All seeded records are demo-only and unverified; confirm eligibility and dates on the official provider website.'
    return {'answer':note,'sources':[{'title':o.title,'url':o.source_url,'demo':o.demo} for o in matches[:5]],'ai_provider':'none — deterministic demo response'}
@app.post('/admin/scholarships',status_code=201)
def add_opportunity(data:OpportunityInput,u:User=Depends(admin),s:Session=Depends(db)):
    o=Opportunity(**{**data.model_dump(exclude={'required_documents'}),'required_documents':__import__('json').dumps(data.required_documents),'provider_name':data.provider_name,'active':True});s.add(o);s.commit();s.refresh(o);return opportunity_json(o)
@app.patch('/admin/scholarships/{opportunity_id}')
def edit_opportunity(opportunity_id:int,data:OpportunityInput,u:User=Depends(admin),s:Session=Depends(db)):
    o=s.get(Opportunity,opportunity_id)
    if not o:raise HTTPException(404,'Opportunity not found')
    for k,v in data.model_dump(exclude={'required_documents'}).items():setattr(o,k,v)
    o.required_documents=__import__('json').dumps(data.required_documents);s.commit();return opportunity_json(o)
@app.post('/admin/verify/{opportunity_id}')
def verify_opportunity(opportunity_id:int,u:User=Depends(admin),s:Session=Depends(db)):
    o=s.get(Opportunity,opportunity_id)
    if not o:raise HTTPException(404,'Opportunity not found')
    if 'https://' not in o.source_url:raise HTTPException(422,'An official HTTPS source is required')
    o.verified=True;o.demo=False;o.last_verified=date.today();s.commit();return opportunity_json(o)
@app.delete('/admin/scholarships/{opportunity_id}')
def archive_opportunity(opportunity_id:int,u:User=Depends(admin),s:Session=Depends(db)):
    o=s.get(Opportunity,opportunity_id)
    if not o:raise HTTPException(404,'Opportunity not found')
    o.active=False;s.commit();return {'archived':True,'id':o.id}

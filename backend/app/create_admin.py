"""Create the first admin account from the terminal (never expose this endpoint)."""
import getpass
from sqlalchemy import select
from .main import SessionLocal,User,password_hash

email=input('Admin email: ').strip().lower()
name=input('Admin name: ').strip()
password=getpass.getpass('Password (minimum 10 characters): ')
if len(password)<10: raise SystemExit('Password must be at least 10 characters.')
with SessionLocal() as session:
    existing=session.scalar(select(User).where(User.email==email))
    if existing: existing.role='admin';print('Existing account promoted to admin.')
    else: session.add(User(email=email,name=name,password_hash=password_hash.hash(password),role='admin'));print('Admin account created.')
    session.commit()

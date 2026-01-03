from .database import engine, Base, SessionLocal
from .models import User
from .auth import get_password_hash

def init_database():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@gmail.com").first()
        if not admin:
            admin = User(
                email="admin@gmail.com",
                hashed_password=get_password_hash("admin@123"),
                full_name="Admin User",
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Admin user created!")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()

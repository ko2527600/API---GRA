"""Update business with correct GRA test credentials"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Business
from app.utils.encryption import encryption_manager
from app.config import settings

# GRA Test Credentials
GRA_TIN = "C00XXXXXXXX"
GRA_COMPANY_NAME = "TEST TAXPAYER 15 PERCENT VAT"
GRA_SECURITY_KEY = "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"

# Create database session
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Get the first business (the one we created)
    business = db.query(Business).first()
    
    if not business:
        print("❌ No business found in database")
        sys.exit(1)
    
    print(f"📝 Updating business: {business.name}")
    print(f"   Current TIN: {business.gra_tin[:20]}...")
    
    # Encrypt and update GRA credentials
    business.gra_tin = encryption_manager.encrypt(GRA_TIN)
    business.gra_company_name = encryption_manager.encrypt(GRA_COMPANY_NAME)
    business.gra_security_key = encryption_manager.encrypt(GRA_SECURITY_KEY)
    
    db.commit()
    
    print(f"✅ Successfully updated GRA credentials!")
    print(f"   TIN: {GRA_TIN}")
    print(f"   Company: {GRA_COMPANY_NAME}")
    print(f"   Security Key: {GRA_SECURITY_KEY}")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error updating credentials: {str(e)}")
    sys.exit(1)
finally:
    db.close()

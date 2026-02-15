"""FastAPI dependency for authentication"""
from fastapi import Depends, Request, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.middleware.auth import AuthMiddleware, AuthenticationError
from app.logger import get_logger

logger = get_logger(__name__)


async def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    FastAPI dependency for authentication verification.
    
    Usage in route:
        @router.post("/api/v1/invoices/submit")
        async def submit_invoice(
            request: Request,
            business: dict = Depends(verify_auth),
            db: Session = Depends(get_db)
        ):
            # business contains: id, name, api_key, status
            ...
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        dict: Business data (id, name, api_key, status)
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        business_data, api_key = await AuthMiddleware.verify_authentication(request, db)
        
        # If public endpoint, return empty dict
        if not api_key:
            return {}
        
        return business_data
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def verify_api_key(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
) -> str:
    """
    FastAPI dependency for API key verification.
    
    Usage in route:
        @router.post("/api/v1/invoices/submit")
        async def submit_invoice(
            submission_data: InvoiceSubmissionSchema,
            db: Session = Depends(get_db),
            api_key: str = Depends(verify_api_key)
        ):
            # api_key is the validated API key
            ...
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    from app.models.models import Business
    
    try:
        # Check if API key exists in database
        business = db.query(Business).filter(Business.api_key == x_api_key).first()
        
        if not business:
            logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        if business.status != "active":
            logger.warning(f"Inactive business attempted access: {business.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business account is not active"
            )
        
        return x_api_key
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during API key verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


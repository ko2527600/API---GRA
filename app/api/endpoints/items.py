"""Item registration, inventory, TIN validation, and tag description endpoints"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.item import (
    ItemRegistrationSchema,
    ItemRegistrationResponseSchema,
    InventoryUpdateSchema,
    InventoryUpdateResponseSchema,
    TINValidationSchema,
    TINValidationResponseSchema,
    TagDescriptionSchema,
    TagDescriptionResponseSchema,
    ItemErrorResponseSchema
)
from app.models.models import (
    Submission, Item, Inventory, TINValidation, TagDescription, Business
)
from app.middleware.auth_dependency import verify_api_key
from app.logger import logger


router = APIRouter(prefix="/items", tags=["items"])


@router.post("/register", response_model=ItemRegistrationResponseSchema, status_code=202)
async def register_item(
    item_data: ItemRegistrationSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Register a new item with GRA
    
    - Validates item data
    - Creates submission record
    - Returns submission ID for tracking
    """
    try:
        submission_id = str(uuid.uuid4())
        
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check if item already exists
        existing_item = db.query(Item).filter(
            Item.business_id == business_obj.id,
            Item.item_ref == item_data.ITEM_REF
        ).first()
        
        if existing_item:
            logger.warning(f"Item {item_data.ITEM_REF} already exists for business {business_obj.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item reference already exists"
            )
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            business_id=business_obj.id,
            submission_type="ITEM",
            submission_status="RECEIVED",
            submitted_at=datetime.utcnow(),
            raw_request=item_data.model_dump()
        )
        
        # Create item record
        item = Item(
            id=str(uuid.uuid4()),
            business_id=business_obj.id,
            item_ref=item_data.ITEM_REF,
            item_name=item_data.ITEM_DESCRIPTION,
            item_category=item_data.ITEM_CATEGORY,
            tax_code=item_data.TAX_CODE,
            gra_registration_status="PENDING"
        )
        
        db.add(submission)
        db.add(item)
        db.commit()
        
        logger.info(f"Item registration submitted: {submission_id}")
        
        return ItemRegistrationResponseSchema(
            submission_id=submission_id,
            item_ref=item_data.ITEM_REF,
            status="RECEIVED",
            submitted_at=submission.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register item"
        )


@router.get("/{item_ref}", response_model=ItemRegistrationResponseSchema)
async def get_item_details(
    item_ref: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get item details by item reference
    
    - Retrieves item registration status
    - Returns GRA item ID if registered
    """
    try:
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Get item
        item = db.query(Item).filter(
            Item.business_id == business_obj.id,
            Item.item_ref == item_ref
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Get submission if exists
        submission = db.query(Submission).filter(
            Submission.business_id == business_obj.id,
            Submission.submission_type == "ITEM"
        ).order_by(Submission.created_at.desc()).first()
        
        status_map = {
            "PENDING": "RECEIVED",
            "REGISTERED": "SUCCESS",
            "FAILED": "FAILED"
        }
        
        return ItemRegistrationResponseSchema(
            submission_id=submission.id if submission else str(uuid.uuid4()),
            item_ref=item.item_ref,
            status=status_map.get(item.gra_registration_status, "RECEIVED"),
            gra_item_id=item.gra_item_id,
            submitted_at=item.created_at,
            completed_at=item.updated_at if item.gra_registration_status != "PENDING" else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving item details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve item details"
        )


@router.post("/inventory/update", response_model=InventoryUpdateResponseSchema, status_code=202)
async def update_inventory(
    inventory_data: InventoryUpdateSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Update inventory quantities
    
    - Validates inventory data
    - Tracks quantity changes
    - Records operation type
    """
    try:
        submission_id = str(uuid.uuid4())
        
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Get item
        item = db.query(Item).filter(
            Item.business_id == business_obj.id,
            Item.item_ref == inventory_data.ITEM_REF
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Get or create inventory record
        inventory = db.query(Inventory).filter(
            Inventory.business_id == business_obj.id,
            Inventory.item_id == item.id
        ).first()
        
        previous_quantity = inventory.quantity if inventory else 0.0
        quantity_change = float(inventory_data.QUANTITY_CHANGE)
        new_quantity = previous_quantity + quantity_change
        
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inventory quantity cannot be negative"
            )
        
        if not inventory:
            inventory = Inventory(
                id=str(uuid.uuid4()),
                business_id=business_obj.id,
                niki_code=f"NIKI-{item.item_ref}-{datetime.utcnow().timestamp()}",
                item_id=item.id,
                quantity=new_quantity,
                gra_sync_status="PENDING"
            )
            db.add(inventory)
        else:
            inventory.quantity = new_quantity
            inventory.last_updated = datetime.utcnow()
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            business_id=business_obj.id,
            submission_type="INVENTORY",
            submission_status="RECEIVED",
            submitted_at=datetime.utcnow(),
            raw_request=inventory_data.model_dump()
        )
        
        db.add(submission)
        db.commit()
        
        logger.info(f"Inventory update submitted: {submission_id}")
        
        return InventoryUpdateResponseSchema(
            submission_id=submission_id,
            item_ref=inventory_data.ITEM_REF,
            status="SUCCESS",
            previous_quantity=str(previous_quantity),
            new_quantity=str(new_quantity),
            updated_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update inventory"
        )


@router.post("/tin/validate", response_model=TINValidationResponseSchema)
async def validate_tin(
    tin_data: TINValidationSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Validate TIN with GRA
    
    - Validates TIN format
    - Caches validation results
    - Returns cached results if not expired
    """
    try:
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check cache
        cached_validation = db.query(TINValidation).filter(
            TINValidation.business_id == business_obj.id,
            TINValidation.tin == tin_data.TIN,
            TINValidation.expires_at > datetime.utcnow()
        ).first()
        
        if cached_validation:
            logger.info(f"TIN validation from cache: {tin_data.TIN}")
            return TINValidationResponseSchema(
                tin=cached_validation.tin,
                is_valid=cached_validation.validation_status == "VALID",
                tin_type=tin_data.TIN_TYPE,
                entity_name=cached_validation.taxpayer_name,
                registration_status="ACTIVE" if cached_validation.validation_status == "VALID" else cached_validation.validation_status,
                gra_response_code=cached_validation.gra_response_code,
                cached=True,
                cache_expires_at=cached_validation.expires_at,
                validated_at=cached_validation.cached_at
            )
        
        # Simulate GRA validation (in production, call actual GRA API)
        is_valid = len(tin_data.TIN) in [11, 15]
        validation_status = "VALID" if is_valid else "INVALID"
        
        # Create cache record
        cache_expiry = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            id=str(uuid.uuid4()),
            business_id=business_obj.id,
            tin=tin_data.TIN,
            validation_status=validation_status,
            taxpayer_name="Sample Taxpayer" if is_valid else None,
            gra_response_code="TIN001" if is_valid else "TIN002",
            cached_at=datetime.utcnow(),
            expires_at=cache_expiry
        )
        
        db.add(tin_validation)
        db.commit()
        
        logger.info(f"TIN validation completed: {tin_data.TIN}")
        
        return TINValidationResponseSchema(
            tin=tin_data.TIN,
            is_valid=is_valid,
            tin_type=tin_data.TIN_TYPE,
            entity_name="Sample Taxpayer" if is_valid else None,
            registration_status="ACTIVE" if is_valid else "INACTIVE",
            gra_response_code="TIN001" if is_valid else "TIN002",
            gra_response_message="TIN is valid" if is_valid else "TIN not found",
            cached=False,
            cache_expires_at=cache_expiry,
            validated_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating TIN: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate TIN"
        )


@router.post("/tags/register", response_model=TagDescriptionResponseSchema, status_code=202)
async def register_tag(
    tag_data: TagDescriptionSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Register tag description with GRA
    
    - Validates tag data
    - Creates submission record
    - Returns submission ID for tracking
    """
    try:
        submission_id = str(uuid.uuid4())
        
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check if tag already exists
        existing_tag = db.query(TagDescription).filter(
            TagDescription.business_id == business_obj.id,
            TagDescription.tag_code == tag_data.TAG_CODE
        ).first()
        
        if existing_tag:
            logger.warning(f"Tag {tag_data.TAG_CODE} already exists for business {business_obj.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag code already exists"
            )
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            business_id=business_obj.id,
            submission_type="TAG_DESCRIPTION",
            submission_status="RECEIVED",
            submitted_at=datetime.utcnow(),
            raw_request=tag_data.model_dump()
        )
        
        # Create tag description record
        tag_description = TagDescription(
            id=str(uuid.uuid4()),
            business_id=business_obj.id,
            tag_code=tag_data.TAG_CODE,
            description=tag_data.TAG_DESCRIPTION,
            category=tag_data.TAG_CATEGORY
        )
        
        db.add(submission)
        db.add(tag_description)
        db.commit()
        
        logger.info(f"Tag registration submitted: {submission_id}")
        
        return TagDescriptionResponseSchema(
            submission_id=submission_id,
            tag_code=tag_data.TAG_CODE,
            status="RECEIVED",
            submitted_at=submission.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register tag"
        )

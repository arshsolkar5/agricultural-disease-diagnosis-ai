from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.diagnosis import DiagnosisRequest
from app.database.engine import get_db
from app.services.diagnosis_service import DiagnosisService
from app.utils.logger import get_logger
from app.utils.exceptions import ValidationException

logger = get_logger("diagnosis_api")
router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])

diagnosis_service = DiagnosisService()

@router.post("", response_model=dict)
async def create_diagnosis(
    request: DiagnosisRequest,
    db: Session = Depends(get_db),
):
    """
    Submit image for diagnosis.
    
    Request:
    {
        "image_base64": "...",
        "crop_type": "rice",
        "farmer_id": "optional",
        "location": "optional"
    }
    
    Response:
    {
        "diagnosis_id": "uuid",
        "trace_id": "uuid",
        "primary_disease": "leaf_blast",
        "confidence": 0.87,
        "observations": [...],
        ...
    }
    """
    try:
        logger.info(
            "diagnosis_request_received",
            crop_type=request.crop_type,
            farmer_id=request.farmer_id,
            additional_context=request.additional_context,
        )
        
        # Validate image
        if not request.image_base64 or len(request.image_base64) < 100:
            raise ValidationException("Invalid or missing image")
        
        # Run diagnosis
        result = await diagnosis_service.diagnose(
            image_b64=request.image_base64,
            crop_type=request.crop_type,
            farmer_id=request.farmer_id,
            location=request.location,
            additional_context=request.additional_context,
            db=db,
        )
        
        logger.info("diagnosis_completed", diagnosis_id=result["diagnosis_id"])
        return result
    
    except ValidationException as e:
        logger.warning("validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("diagnosis_error", error=str(e))
        raise HTTPException(status_code=500, detail="Diagnosis failed")

@router.get("/{diagnosis_id}")
async def get_diagnosis(
    diagnosis_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve diagnosis by ID."""
    try:
        result = diagnosis_service.get_diagnosis(diagnosis_id, db)
        
        if not result:
            raise HTTPException(status_code=404, detail="Diagnosis not found")
        
        return result
    
    except Exception as e:
        logger.error("get_diagnosis_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve diagnosis")

@router.get("/farmer/{farmer_id}/history")
async def get_farmer_diagnoses(
    farmer_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get diagnosis history for farmer."""
    try:
        diagnoses = diagnosis_service.get_farmer_diagnoses(farmer_id, db, limit)
        return {"diagnoses": diagnoses, "count": len(diagnoses)}
    
    except Exception as e:
        logger.error("get_history_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

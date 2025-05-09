from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
import json
import uuid
from datetime import datetime
import traceback

from ..models.indicator import CustomIndicator, IndicatorParameter
from ..services.indicator_service import IndicatorService, StandardIndicatorWrapper
from ..utils.validation import validate_indicator_code, validate_indicator_parameters
from ..config import TEMP_DATA_DIR, DATA_DIR

router = APIRouter(prefix="/indicators", tags=["indicators"])
indicator_service = IndicatorService()

# Standard indicator models
class StandardIndicatorDefinition(BaseModel):
    id: str
    name: str
    category: str
    description: str
    parameters: List[IndicatorParameter]
    inputs: List[str]
    outputs: List[str]
    source_library: str

class StandardIndicatorCategory(BaseModel):
    id: str
    name: str
    description: str
    indicators: List[StandardIndicatorDefinition]

class StandardIndicator(BaseModel):
    definition_id: str
    name: str
    parameters: Dict[str, Any]
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StandardIndicatorTestRequest(BaseModel):
    definition_id: str
    parameters: Dict[str, Any]
    test_data: bool = True
    include_price: bool = False

# Routes for custom indicators (existing)
@router.get("/", response_model=List[CustomIndicator])
async def get_indicators():
    try:
        return indicator_service.get_all_indicators()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Dict[str, Any])
async def create_indicator(indicator: CustomIndicator = Body(...)):
    try:
        # Validate indicator code
        validation_result = validate_indicator_code(indicator.code)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Validate parameters
        param_validation = validate_indicator_parameters(indicator.parameters)
        if not param_validation["valid"]:
            raise HTTPException(status_code=400, detail=param_validation["error"])
        
        # Create indicator
        indicator_id = indicator_service.create_indicator(indicator)
        return {"id": indicator_id, "success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create indicator: {str(e)}")

# Other existing routes...

# New routes for standard indicators from libraries like pandas-ta

@router.get("/standard-catalog", response_model=List[StandardIndicatorCategory])
async def get_standard_indicators_catalog():
    """Get the catalog of available standard indicators."""
    try:
        # In a real implementation, this would come from a database or config
        # Here we're hardcoding for simplicity
        categories = indicator_service.get_standard_indicators_catalog()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/standard/test", response_model=Dict[str, Any])
async def test_standard_indicator(request: StandardIndicatorTestRequest = Body(...)):
    """Test a standard indicator with the given parameters."""
    try:
        # Get the indicator definition
        definition = indicator_service.get_standard_indicator_definition(request.definition_id)
        if not definition:
            raise HTTPException(status_code=404, detail=f"Indicator definition not found: {request.definition_id}")
        
        # Validate parameters
        param_validation = validate_indicator_parameters(request.parameters)
        if not param_validation["valid"]:
            raise HTTPException(status_code=400, detail=param_validation["error"])
        
        # Generate test data if needed
        if request.test_data:
            # Generate sample data for testing
            sample_data = indicator_service.generate_sample_data(
                include_price=request.include_price
            )
            
            # Calculate the indicator
            result = indicator_service.calculate_standard_indicator(
                definition_id=request.definition_id,
                parameters=request.parameters,
                data=sample_data
            )
            
            return {
                "success": True,
                "preview": result,
                "dates": sample_data.index.astype(str).tolist() if isinstance(sample_data.index, pd.DatetimeIndex) else None,
                "price_data": {
                    "open": sample_data["open"].tolist() if "open" in sample_data.columns and request.include_price else None,
                    "high": sample_data["high"].tolist() if "high" in sample_data.columns and request.include_price else None,
                    "low": sample_data["low"].tolist() if "low" in sample_data.columns and request.include_price else None,
                    "close": sample_data["close"].tolist() if "close" in sample_data.columns and request.include_price else None,
                    "volume": sample_data["volume"].tolist() if "volume" in sample_data.columns and request.include_price else None
                } if request.include_price else None
            }
        
        return {"success": True, "message": "Indicator definition is valid"}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": f"Error testing indicator: {str(e)}"}

@router.post("/standard/save", response_model=Dict[str, Any])
async def save_standard_indicator(indicator: StandardIndicator = Body(...)):
    """Save a configured standard indicator for future use."""
    try:
        # Get the indicator definition
        definition = indicator_service.get_standard_indicator_definition(indicator.definition_id)
        if not definition:
            raise HTTPException(status_code=404, detail=f"Indicator definition not found: {indicator.definition_id}")
        
        # Validate parameters
        param_validation = validate_indicator_parameters(indicator.parameters)
        if not param_validation["valid"]:
            raise HTTPException(status_code=400, detail=param_validation["error"])
        
        # Save the configured indicator
        indicator_id = indicator_service.save_standard_indicator(indicator)
        
        return {"id": indicator_id, "success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save indicator: {str(e)}") 
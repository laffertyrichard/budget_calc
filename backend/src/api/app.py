# api/app.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import logging
import json
from datetime import datetime

from src.core.estimation_engine import EstimationEngine
from src.core.estimation_engine import EnhancedEstimationEngine
from src.utils.report_generator import ReportGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Construction Budget Calculator API")

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the project data model
class RoomTradeConfig(BaseModel):
    tier: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class Room(BaseModel):
    name: str
    type: str
    square_footage: float
    tier: Optional[str] = None
    trades: Optional[Dict[str, RoomTradeConfig]] = None

class ProjectData(BaseModel):
    square_footage: float
    tier: Optional[str] = None
    global_tier: Optional[str] = None
    project_name: Optional[str] = None
    construction_type: Optional[str] = None
    bedroom_count: Optional[int] = None
    primary_bath_count: Optional[int] = None
    secondary_bath_count: Optional[int] = None
    powder_room_count: Optional[int] = None
    rooms: Optional[Dict[str, Room]] = None
    trades: Optional[Dict[str, str]] = None
    additional_parameters: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    is_valid: bool
    missing_fields: List[str] = []
    invalid_values: List[Dict[str, Any]] = []
    warnings: List[str] = []

# Dependency to get engine instances
def get_standard_engine():
    return EstimationEngine()

def get_enhanced_engine():
    return EnhancedEstimationEngine()

def get_report_generator():
    return ReportGenerator()

# API endpoints
@app.get("/api/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/estimate")
async def create_estimate(
    project_data: ProjectData,
    engine: EstimationEngine = Depends(get_standard_engine)
):
    """Create a standard estimate"""
    try:
        # Convert to dictionary for the engine
        data_dict = project_data.dict(exclude_none=True)
        
        # Run estimation
        result = engine.estimate_project(data_dict)
        return result
    except Exception as e:
        logger.error(f"Error creating estimate: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/estimate/detailed")
async def create_detailed_estimate(
    project_data: ProjectData,
    engine: EnhancedEstimationEngine = Depends(get_enhanced_engine)
):
    """Create a detailed estimate with room and trade customizations"""
    try:
        # Convert to dictionary for the engine
        data_dict = project_data.dict(exclude_none=True)
        
        # Run detailed estimation
        result = engine.estimate_detailed_project(data_dict)
        return result
    except Exception as e:
        logger.error(f"Error creating detailed estimate: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/estimate/validate")
async def validate_project_data(
    project_data: ProjectData,
    engine: EstimationEngine = Depends(get_standard_engine)
):
    """Validate project data before estimation"""
    try:
        # Convert to dictionary for the engine
        data_dict = project_data.dict(exclude_none=True)
        
        # Validate data
        validation_result = engine.validate_project_data(data_dict)
        return validation_result
    except Exception as e:
        logger.error(f"Error validating project data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save/{name}")
async def save_estimation(
    name: str,
    estimation_data: Dict[str, Any],
    engine: EstimationEngine = Depends(get_standard_engine)
):
    """Save an estimation result"""
    try:
        success = engine.save_estimation(estimation_data, name)
        if success:
            return {"status": "success", "message": f"Estimation saved as '{name}'"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save estimation")
    except Exception as e:
        logger.error(f"Error saving estimation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/load/{name}")
async def load_estimation(
    name: str,
    engine: EstimationEngine = Depends(get_standard_engine)
):
    """Load a saved estimation"""
    try:
        estimation = engine.load_estimation(name)
        if estimation:
            return estimation
        else:
            raise HTTPException(status_code=404, detail=f"Estimation '{name}' not found")
    except Exception as e:
        logger.error(f"Error loading estimation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list-saved")
async def list_saved_estimations(
    engine: EstimationEngine = Depends(get_standard_engine)
):
    """List all saved estimations"""
    try:
        # This would need to be implemented in the engine
        estimations_dir = engine.config.get('data', {}).get('estimations_path', 'data/estimations')
        import os
        import glob
        from pathlib import Path
        
        estimates = []
        for file_path in glob.glob(os.path.join(estimations_dir, "*.json")):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                name = Path(file_path).stem
                stat = os.stat(file_path)
                
                estimates.append({
                    "name": name,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size,
                    "project": data.get("project", {}),
                    "total_cost": data.get("total_cost", 0)
                })
            except Exception as e:
                logger.warning(f"Error reading estimation file {file_path}: {str(e)}")
        
        return {"estimates": estimates, "count": len(estimates)}
    except Exception as e:
        logger.error(f"Error listing saved estimations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configuration/tiers")
async def get_tiers(
    engine: EstimationEngine = Depends(get_standard_engine)
):
    """Get available construction tiers"""
    try:
        tiers = engine.config.get('estimation', {}).get('tiers', {})
        return {"tiers": tiers}
    except Exception as e:
        logger.error(f"Error getting tiers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configuration/trades")
async def get_trade_categories():
    """Get available trade categories"""
    try:
        # This would be loaded from a configuration file in practice
        trades = [
            {
                "id": "electrical", 
                "name": "Electrical",
                "description": "Electrical systems and fixtures"
            },
            {
                "id": "plumbing", 
                "name": "Plumbing",
                "description": "Plumbing fixtures and systems"
            },
            {
                "id": "hvac", 
                "name": "HVAC",
                "description": "Heating, ventilation, and air conditioning"
            },
            {
                "id": "cabinetry", 
                "name": "Cabinetry",
                "description": "Cabinets and millwork"
            },
            {
                "id": "countertops", 
                "name": "Countertops",
                "description": "Countertop materials and installation"
            },
            {
                "id": "tile", 
                "name": "Tile",
                "description": "Tile materials and installation"
            },
            {
                "id": "drywall_interior", 
                "name": "Drywall & Interior",
                "description": "Interior wall finishes"
            },
            {
                "id": "painting_coatings", 
                "name": "Painting & Coatings",
                "description": "Paint and surface finishes"
            },
            {
                "id": "finish_carpentry", 
                "name": "Finish Carpentry",
                "description": "Trim, molding, and finish woodwork"
            }
        ]
        return {"trades": trades}
    except Exception as e:
        logger.error(f"Error getting trade categories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report/{estimate_id}")
async def generate_report(
    estimate_id: str,
    format: str = "summary",
    engine: EstimationEngine = Depends(get_standard_engine),
    report_generator: ReportGenerator = Depends(get_report_generator)
):
    """Generate a report for a saved estimate"""
    try:
        # Load the estimation
        estimation = engine.load_estimation(estimate_id)
        if not estimation:
            raise HTTPException(status_code=404, detail=f"Estimation '{estimate_id}' not found")
        
        # Generate the report based on the requested format
        if format == "summary":
            report = report_generator.generate_summary_report(estimation)
            return {"report": report}
        elif format == "detailed":
            report = report_generator.generate_detailed_report(estimation)
            return {"report": report}
        elif format == "csv":
            from fastapi.responses import StreamingResponse
            import io
            
            # Generate CSV and return as attachment
            df = report_generator.generate_csv_report(estimation)
            stream = io.StringIO()
            df.to_csv(stream, index=False)
            
            response = StreamingResponse(
                iter([stream.getvalue()]), 
                media_type="text/csv"
            )
            response.headers["Content-Disposition"] = f"attachment; filename=estimate_{estimate_id}.csv"
            return response
        else:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {format}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Run the app with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
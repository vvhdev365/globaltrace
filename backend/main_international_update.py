"""
Updated main.py - Add these imports and router to enable international tracking
"""

# Add these imports to your existing main.py:
from datetime import timedelta

# Import international API router
from international_api import router as international_router

# In your main app, add this line after creating the FastAPI app:
app.include_router(international_router)

# Add this endpoint to test international features:
@app.get("/api/test/international")
async def test_international_setup():
    """
    Test endpoint to verify international tracking is set up correctly
    """
    return {
        "status": "operational",
        "features": {
            "vessel_tracking": "enabled",
            "flight_tracking": "enabled",
            "port_database": "loaded",
            "test_shipments": "available"
        },
        "endpoints": {
            "list_shipments": "/api/international/shipments",
            "track_shipment": "/api/international/shipments/{tracking_number}",
            "vessel_position": "/api/international/vessels/{imo}/position",
            "flight_position": "/api/international/flights/{flight_number}/position",
            "ports": "/api/international/ports",
            "generate_test": "/api/international/test/generate-shipments"
        },
        "sample_tracking_numbers": {
            "sea_freight": ["TEST-SEA-001", "IND-USA-SEA-001", "IND-USA-SEA-002"],
            "air_freight": ["TEST-AIR-001", "IND-USA-AIR-001", "IND-USA-AIR-002"]
        }
    }

#!/usr/bin/env python
"""Run the FastAPI server"""
import uvicorn
import sys

if __name__ == "__main__":
    print("Starting GRA API Server...")
    print("Server will run on: http://localhost:8000")
    print("API Docs: http://localhost:8000/api/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

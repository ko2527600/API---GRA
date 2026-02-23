"""Middleware to cache request body for multiple reads"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders


class BodyCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware that caches the request body so it can be read multiple times.
    
    This is necessary for signature verification which needs to read the body,
    while still allowing the endpoint to read it again.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Cache the request body before passing to next middleware/endpoint"""
        # Read the body
        body = await request.body()
        
        # Create a new receive callable that returns the cached body
        async def receive():
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
        
        # Replace the receive callable
        request._receive = receive
        
        # Continue with the request
        response = await call_next(request)
        return response

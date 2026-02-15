# GRA E-VAT API - Business Registration Page

## Overview

A professional, user-friendly registration page has been created for businesses to register and obtain their API credentials.

## Accessing the Registration Page

Once the API server is running, businesses can access the registration page at:

```
http://localhost:8000/register
```

## Features

### 1. **Business Registration Form**
   - Business Name
   - GRA TIN (Tax Identification Number)
   - GRA Company Name
   - GRA Security Key

### 2. **Real-time Validation**
   - TIN length validation (11-15 characters)
   - Required field validation
   - Client-side error handling

### 3. **API Integration**
   - Automatically calls the `/api/v1/api-keys/generate` endpoint
   - Handles registration errors gracefully
   - Shows loading state during processing

### 4. **Credentials Display**
   After successful registration, businesses receive:
   - **API Key**: Used in `X-API-Key` header for authentication
   - **API Secret**: Used to generate HMAC signatures (store securely)
   - **Business ID**: Unique identifier for the business

### 5. **Security Features**
   - Password field for GRA Security Key (masked input)
   - Warning about API Secret storage
   - Copy-to-clipboard functionality for credentials
   - Download credentials as text file

### 6. **User Experience**
   - Modern, responsive design
   - Works on desktop and mobile devices
   - Clear error messages
   - Loading indicators
   - Success confirmations

## How It Works

### Registration Flow

1. **User fills form** with business details
2. **Form validation** checks all required fields
3. **API call** to `/api/v1/api-keys/generate` endpoint
4. **Credentials generated** by backend
5. **Display credentials** with copy and download options
6. **User stores** credentials securely

### API Endpoint Called

```
POST /api/v1/api-keys/generate

Request Body:
{
  "business_name": "ABC Company Ltd",
  "gra_tin": "C00XXXXXXXX",
  "gra_company_name": "ABC COMPANY LTD",
  "gra_security_key": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
}

Response:
{
  "api_key": "sk_live_...",
  "api_secret": "secret_...",
  "business_id": "uuid-...",
  "business_name": "ABC Company Ltd",
  "created_at": "2026-02-14T10:00:00Z"
}
```

## Customization

### Styling
The page uses inline CSS that can be customized by editing `app/static/register.html`:
- Colors: Change `#667eea` and `#764ba2` for the gradient
- Fonts: Modify the `font-family` in the `body` style
- Layout: Adjust padding and margins in `.container`

### Form Fields
To add or remove fields, edit the form section in the HTML and update the JavaScript `registerBusiness()` function.

### API Endpoint
If the API is hosted on a different server, update the `API_BASE_URL` in the JavaScript:

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api/v1';
```

## Security Considerations

1. **HTTPS Only**: In production, always use HTTPS
2. **CORS Configuration**: Ensure CORS is properly configured in `app/config.py`
3. **API Secret**: Never expose the API Secret in logs or responses
4. **Rate Limiting**: The API has rate limiting to prevent abuse
5. **Input Validation**: All inputs are validated on both client and server

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### "Registration failed: Failed to fetch"
- Check if the API server is running
- Verify CORS is enabled
- Check browser console for detailed errors

### "Registration failed: Business with this TIN already exists"
- The TIN is already registered
- Use a different TIN or contact support

### Credentials not displaying
- Check browser console for JavaScript errors
- Verify the API response format
- Clear browser cache and try again

## Next Steps After Registration

1. **Store Credentials Securely**
   - Save the API Key and Secret in a secure location
   - Never commit credentials to version control

2. **Generate HMAC Signatures**
   - Use the API Secret to generate HMAC-SHA256 signatures
   - Include signature in `X-API-Signature` header

3. **Make API Requests**
   - Use API Key in `X-API-Key` header
   - Include HMAC signature in `X-API-Signature` header
   - Send requests to `/api/v1/invoices/submit`, etc.

4. **Read Documentation**
   - Visit `/api/docs` for interactive API documentation
   - Check `/api/redoc` for ReDoc documentation

## Support

For issues or questions:
- Check the API documentation at `/api/docs`
- Review error messages carefully
- Contact support with your Business ID

---

**Version**: 1.0.0  
**Last Updated**: February 2026

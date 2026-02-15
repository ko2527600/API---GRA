# Quick Start - Business Registration Page

## 🚀 Getting Started

### Step 1: Start the API Server

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the server
python -m uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

### Step 2: Access the Registration Page

Open your browser and go to:

```
http://localhost:8000/register
```

You should see a professional registration form.

## 📝 Registration Form Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Business Name** | Your company's registered name | ABC Company Ltd |
| **GRA TIN** | Tax Identification Number (11-15 chars) | C00XXXXXXXX |
| **GRA Company Name** | Name as registered with GRA |  ABCCOMPANY LTD |
| **GRA Security Key** | Your GRA security key | UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH |

## ✅ Registration Process

1. **Fill the form** with your business details
2. **Click "Register Business"** button
3. **Wait for processing** (shows loading spinner)
4. **Receive credentials**:
   - API Key
   - API Secret
   - Business ID

## 🔐 After Registration

### Store Your Credentials

```
API Key: sk_live_abc123...
API Secret: secret_xyz789...
Business ID: 550e8400-e29b-41d4-a716-446655440000
```

**⚠️ Important**: Store your API Secret securely. You won't be able to retrieve it again!

### Download Credentials

Click "Download Credentials" to save a text file with your credentials.

### Use Your Credentials

To make API requests, include:

```bash
curl -X POST http://localhost:8000/api/v1/invoices/submit \
  -H "X-API-Key: sk_live_abc123..." \
  -H "X-API-Signature: <hmac_signature>" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 🔗 Useful Links

- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc Documentation**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health
- **Registration Page**: http://localhost:8000/register

## 🛠️ Troubleshooting

### Page not loading?
- Ensure the API server is running
- Check that you're using `http://` (not `https://`)
- Clear browser cache

### Registration fails?
- Check all fields are filled correctly
- Verify TIN is 11-15 characters
- Check browser console for error details

### Can't copy credentials?
- Try using the "Download Credentials" button instead
- Check browser permissions for clipboard access

## 📚 Next Steps

1. **Read the API Documentation**
   - Visit http://localhost:8000/api/docs
   - Try out endpoints in the interactive UI

2. **Generate HMAC Signatures**
   - Use your API Secret to sign requests
   - See documentation for signature generation

3. **Submit Your First Invoice**
   - Use the `/api/v1/invoices/submit` endpoint
   - Include proper authentication headers

4. **Set Up Webhooks** (Optional)
   - Register webhook URLs for notifications
   - Receive updates on submission status

## 💡 Tips

- **Save credentials securely**: Use a password manager
- **Rotate credentials**: Periodically revoke and regenerate
- **Monitor usage**: Check API documentation for rate limits
- **Test first**: Use test environment before production

## 📞 Support

For issues or questions:
1. Check the API documentation at `/api/docs`
2. Review error messages in the browser console
3. Check the REGISTRATION_PAGE.md for detailed information

---

**Ready to get started?** Open http://localhost:8000/register in your browser!

# Task Queue Quick Start Guide

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install and start Redis:
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis-server

# Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis:latest
```

## Configuration

Set environment variables in `.env`:

```bash
# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_ENABLED=true

# Retry
MAX_RETRIES=5
RETRY_BACKOFF_BASE=1
RETRY_BACKOFF_MAX=3600

# Submission
SUBMISSION_PROCESSING_TIMEOUT=300
```

## Running the System

### Terminal 1: Start API Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Celery Worker

```bash
python -m celery -A app.services.task_queue worker --loglevel=info
```

### Terminal 3: Monitor Tasks (Optional)

```bash
# View active tasks
celery -A app.services.task_queue inspect active

# View worker stats
celery -A app.services.task_queue inspect stats

# View pending tasks
celery -A app.services.task_queue inspect reserved
```

## Using the Task Queue

### Queue a Submission

```python
from app.services.submission_queue_integration import SubmissionQueueIntegration

integration = SubmissionQueueIntegration()

# Queue JSON submission
task_id = integration.queue_submission(
    submission_id="uuid-123",
    business_id=business.id,
    submission_type="INVOICE",
    request_data={
        "company": {...},
        "header": {...},
        "item_list": [...]
    },
    content_type="application/json",
    priority=5,
)

print(f"Task queued: {task_id}")
```

### Check Task Status

```python
status = integration.get_submission_status(task_id)

print(f"Status: {status['status']}")
print(f"Result: {status['result']}")
print(f"Error: {status['error']}")
```

### Cancel a Task

```python
success = integration.cancel_submission(task_id)
print(f"Cancelled: {success}")
```

## API Endpoints

### Submit Invoice

```bash
curl -X POST http://localhost:8000/api/v1/invoices/submit \
  -H "X-API-Key: your-api-key" \
  -H "X-API-Signature: your-signature" \
  -H "Content-Type: application/json" \
  -d '{
    "company": {...},
    "header": {...},
    "item_list": [...]
  }'

# Response (202 Accepted)
{
  "submission_id": "uuid-123",
  "status": "RECEIVED",
  "message": "Invoice received and queued for GRA processing"
}
```

### Check Status

```bash
curl -X GET http://localhost:8000/api/v1/invoices/uuid-123/status \
  -H "X-API-Key: your-api-key" \
  -H "X-API-Signature: your-signature"

# Response
{
  "submission_id": "uuid-123",
  "status": "SUCCESS",
  "gra_invoice_id": "GRA-INV-2026-001",
  "gra_qr_code": "https://...",
  "processing_time_ms": 5000
}
```

## Testing

### Run Tests

```bash
# All tests
pytest tests/test_task_queue.py -v

# Specific test
pytest tests/test_task_queue.py::TestTaskQueueManager::test_queue_json_submission -v

# With coverage
pytest tests/test_task_queue.py --cov=app.services.task_queue
```

### Manual Testing

1. Start API and worker
2. Submit a test invoice
3. Check status immediately (should be RECEIVED)
4. Wait a few seconds
5. Check status again (should be PROCESSING or SUCCESS)

## Troubleshooting

### Worker Not Processing Tasks

```bash
# Check if worker is running
celery -A app.services.task_queue inspect active

# Check Redis connection
redis-cli ping

# Restart worker
# Kill the worker process and restart
```

### Tasks Stuck in PENDING

```bash
# Check worker logs for errors
# Verify Redis is accessible
# Check task timeout settings
# Restart worker if necessary
```

### High Memory Usage

```bash
# Reduce worker concurrency
python -m celery -A app.services.task_queue worker --concurrency=2

# Increase max tasks per child
python -m celery -A app.services.task_queue worker --max-tasks-per-child=500
```

## Common Commands

```bash
# Start worker with custom concurrency
python -m celery -A app.services.task_queue worker --concurrency=4

# View active tasks
celery -A app.services.task_queue inspect active

# View registered tasks
celery -A app.services.task_queue inspect registered

# View worker stats
celery -A app.services.task_queue inspect stats

# Purge all pending tasks
celery -A app.services.task_queue purge

# View task result
celery -A app.services.task_queue result <task-id>

# Revoke a task
celery -A app.services.task_queue revoke <task-id>
```

## Performance Tips

1. **Increase concurrency** for higher throughput:
   ```bash
   --concurrency=8
   ```

2. **Run multiple workers** for redundancy:
   ```bash
   # Terminal 2
   python -m celery -A app.services.task_queue worker --concurrency=4
   
   # Terminal 3
   python -m celery -A app.services.task_queue worker --concurrency=4
   ```

3. **Monitor queue depth** to detect bottlenecks:
   ```bash
   celery -A app.services.task_queue inspect reserved
   ```

4. **Use Redis persistence** for durability:
   ```bash
   # In redis.conf
   save 900 1
   appendonly yes
   ```

## Next Steps

1. Read [ASYNC_TASK_QUEUE.md](./ASYNC_TASK_QUEUE.md) for detailed documentation
2. Review [requirements.md](./requirements.md) for async processing requirements
3. Check [design.md](./design.md) for architecture details
4. Explore test cases in `tests/test_task_queue.py`

## Support

For issues or questions:
1. Check logs: `celery -A app.services.task_queue inspect active`
2. Review error details in database
3. Check Redis connection: `redis-cli ping`
4. Restart worker and try again

# Async Task Queue Implementation

## Overview

The async task queue is a Celery-based system that handles asynchronous processing of GRA submissions. It enables the API to accept submissions immediately (202 Accepted) and process them in the background, improving responsiveness and reliability.

## Architecture

### Components

1. **Celery App** (`app/services/task_queue.py`)
   - Celery application instance
   - Task definitions
   - Retry logic and error handling

2. **Task Queue Manager** (`app/services/task_queue.py`)
   - High-level API for queuing submissions
   - Task status tracking
   - Task cancellation

3. **Submission Queue Integration** (`app/services/submission_queue_integration.py`)
   - Integration layer for API endpoints
   - Handles JSON/XML submissions
   - Priority management

4. **Celery Worker** (`app/worker.py`)
   - Worker process that executes tasks
   - Configurable concurrency
   - Automatic retry handling

### Data Flow

```
API Request
    ↓
Create Submission Record (RECEIVED)
    ↓
Queue Task (Celery)
    ↓
Return 202 Accepted
    ↓
Worker Picks Up Task
    ↓
Update Status (PROCESSING)
    ↓
Submit to GRA
    ↓
Update Status (PENDING_GRA/SUCCESS/FAILED)
    ↓
Business Polls Status or Receives Webhook
```

## Configuration

### Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_ENABLED=true

# Retry Configuration
MAX_RETRIES=5
RETRY_BACKOFF_BASE=1
RETRY_BACKOFF_MAX=3600

# Submission Processing
SUBMISSION_PROCESSING_TIMEOUT=300
SUBMISSION_POLLING_INTERVAL=5
SUBMISSION_POLLING_MAX_ATTEMPTS=60
```

### Celery Configuration

The Celery app is configured in `app/services/task_queue.py`:

```python
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=290,  # 4m 50s
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
```

## Task Definitions

### JSON Submission Task

```python
@celery_app.task(
    base=SubmissionTask,
    bind=True,
    name="process_json_submission",
)
def process_json_submission_task(
    self,
    submission_id: str,
    business_id: str,
    request_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Process JSON submission to GRA"""
```

**Behavior:**
- Accepts JSON submission data
- Injects GRA credentials
- Submits to GRA API
- Updates submission status
- Retries on transient errors
- Fails on permanent errors

### XML Submission Task

```python
@celery_app.task(
    base=SubmissionTask,
    bind=True,
    name="process_xml_submission",
)
def process_xml_submission_task(
    self,
    submission_id: str,
    business_id: str,
    request_data: str,
) -> Dict[str, Any]:
    """Process XML submission to GRA"""
```

**Behavior:**
- Accepts XML submission data
- Injects GRA credentials
- Submits to GRA API
- Updates submission status
- Retries on transient errors
- Fails on permanent errors

## Retry Logic

### Retry Strategy

The task queue implements intelligent retry logic based on error classification:

#### Transient Errors (Retryable)
- Network timeouts
- HTTP 5xx errors
- GRA service unavailable (D06, A13, IS100)
- Rate limiting (429)

**Retry Strategy:**
- Max retries: 5
- Backoff: 1s, 2s, 4s, 8s, 16s
- Total window: ~30 seconds

#### Permanent Errors (Not Retryable)
- Validation errors (B16, B18, B20, etc.)
- Authentication errors (A01, B01)
- Invalid data (B05, B051, B07, etc.)

**Behavior:**
- No retry
- Fail immediately
- Return error to business

#### Service Unavailable (Extended Retry)
- GRA service down (D06)
- Database unavailable (A13)

**Retry Strategy:**
- Max retries: 10
- Backoff: 5s, 10s, 20s, 40s, 80s, 160s, 320s, 640s, 1280s, 2560s
- Total window: ~1 hour

### Error Classification

```python
class GRAErrorClassifier:
    """Classifies errors to determine retry strategy"""
    
    TRANSIENT_ERROR_CODES = {"D06", "IS100", "A13"}
    PERMANENT_ERROR_CODES = {"A01", "B01", "B05", ...}
    TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}
```

## Task Queue Manager API

### Queue Submission

```python
manager = TaskQueueManager()

# Queue JSON submission
task_id = manager.queue_json_submission(
    submission_id="uuid-123",
    business_id="uuid-456",
    request_data={...},
    priority=5,  # 0-10, higher = more important
)

# Queue XML submission
task_id = manager.queue_xml_submission(
    submission_id="uuid-123",
    business_id="uuid-456",
    request_data="<xml>...</xml>",
    priority=5,
)
```

### Get Task Status

```python
status = manager.get_task_status("task-id")

# Returns:
{
    "task_id": "task-id",
    "status": "PENDING|STARTED|SUCCESS|FAILURE|RETRY",
    "result": {...},  # if successful
    "error": "error message",  # if failed
}
```

### Cancel Task

```python
success = manager.cancel_task("task-id")
```

## Submission Queue Integration

### Queue Submission from Endpoint

```python
from app.services.submission_queue_integration import SubmissionQueueIntegration

integration = SubmissionQueueIntegration()

task_id = integration.queue_submission(
    submission_id="uuid-123",
    business_id=business.id,
    submission_type="INVOICE",
    request_data={...},
    content_type="application/json",
    priority=5,
)
```

### Get Submission Status

```python
status = integration.get_submission_status(task_id)
```

### Cancel Submission

```python
success = integration.cancel_submission(task_id)
```

## Running the Worker

### Start Worker

```bash
# Start Celery worker
python -m celery -A app.services.task_queue worker --loglevel=info

# Or use the worker script
python app/worker.py

# With custom concurrency
python -m celery -A app.services.task_queue worker --loglevel=info --concurrency=4
```

### Worker Configuration

```bash
# Concurrency (number of worker processes)
--concurrency=4

# Prefetch multiplier (tasks per worker)
--prefetch-multiplier=1

# Max tasks per child (restart after N tasks)
--max-tasks-per-child=1000

# Log level
--loglevel=info
```

### Monitor Worker

```bash
# View active tasks
celery -A app.services.task_queue inspect active

# View registered tasks
celery -A app.services.task_queue inspect registered

# View worker stats
celery -A app.services.task_queue inspect stats

# Purge queue (remove all pending tasks)
celery -A app.services.task_queue purge
```

## Submission Status Lifecycle

```
RECEIVED
  ↓ (Task queued)
PROCESSING
  ↓ (Sent to GRA)
PENDING_GRA
  ↓ (GRA response received)
SUCCESS (or FAILED)
```

### Status Meanings

- **RECEIVED**: Submission received by API, queued for processing
- **PROCESSING**: Task started, validating and preparing for GRA
- **PENDING_GRA**: Sent to GRA, awaiting response
- **SUCCESS**: GRA accepted and stamped
- **FAILED**: GRA rejected or processing error

## Error Handling

### Task Failure Handling

When a task fails after all retries:

1. Submission status updated to FAILED
2. Error details stored in database
3. Error logged with full context
4. Webhook notification sent (if configured)
5. Business can query status for error details

### Error Details Storage

```python
submission.error_details = {
    "error": "error message",
    "error_type": "TASK_FAILURE|GRA_ERROR|VALIDATION_ERROR",
    "retry_count": 5,
    "response_data": {...},
}
```

## Monitoring & Logging

### Task Logging

All tasks log:
- Task start/completion
- Retry attempts
- Error details
- Processing time
- Business ID for multi-tenancy

### Log Format

```json
{
    "timestamp": "2026-02-10T10:00:00Z",
    "level": "INFO",
    "message": "Processing JSON submission task: uuid-123",
    "submission_id": "uuid-123",
    "business_id": "uuid-456",
    "task_id": "json-uuid-123",
    "retry_count": 0
}
```

### Monitoring Metrics

- Task queue depth (pending tasks)
- Task success rate
- Task failure rate
- Average processing time
- Retry rate
- Worker utilization

## Performance Considerations

### Throughput

- **Concurrency**: 4 workers by default (configurable)
- **Tasks per worker**: 1 (prefetch_multiplier=1)
- **Throughput**: ~240 submissions/hour with 4 workers

### Scaling

To increase throughput:

1. Increase worker concurrency:
   ```bash
   --concurrency=8
   ```

2. Add more worker processes:
   ```bash
   # Run multiple worker instances
   python -m celery -A app.services.task_queue worker --concurrency=4
   python -m celery -A app.services.task_queue worker --concurrency=4
   ```

3. Use Redis cluster for broker/backend

### Resource Usage

- **Memory per worker**: ~50-100MB
- **CPU**: Minimal (mostly I/O bound)
- **Redis**: ~10MB for queue state

## Troubleshooting

### Tasks Not Processing

1. Check worker is running:
   ```bash
   celery -A app.services.task_queue inspect active
   ```

2. Check Redis connection:
   ```bash
   redis-cli ping
   ```

3. Check task queue:
   ```bash
   celery -A app.services.task_queue inspect reserved
   ```

### Tasks Stuck in PENDING

1. Check worker logs for errors
2. Verify Redis is accessible
3. Check task timeout settings
4. Restart worker if necessary

### High Retry Rate

1. Check GRA API availability
2. Review error logs for patterns
3. Verify network connectivity
4. Check rate limiting

### Memory Issues

1. Reduce worker concurrency
2. Reduce prefetch multiplier
3. Increase max_tasks_per_child
4. Monitor Redis memory usage

## Best Practices

1. **Always use task IDs**: Enables tracking and cancellation
2. **Monitor queue depth**: Alert if queue grows too large
3. **Set appropriate timeouts**: Prevent stuck tasks
4. **Use priority wisely**: Reserve high priority for urgent submissions
5. **Monitor error rates**: Track and investigate failures
6. **Scale horizontally**: Add more workers as needed
7. **Use Redis persistence**: Enable AOF for durability
8. **Regular backups**: Backup Redis data regularly

## Integration with API Endpoints

### Example: Invoice Submission

```python
@router.post("/submit", status_code=202)
async def submit_invoice(
    submission_data: InvoiceSubmissionSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Create submission record
    submission = Submission(...)
    db.add(submission)
    db.commit()
    
    # Queue for async processing
    from app.services.submission_queue_integration import SubmissionQueueIntegration
    integration = SubmissionQueueIntegration()
    
    task_id = integration.queue_submission(
        submission_id=submission.id,
        business_id=business.id,
        submission_type="INVOICE",
        request_data=submission_data.model_dump(),
        content_type="application/json",
    )
    
    return {
        "submission_id": submission.id,
        "status": "RECEIVED",
        "message": "Invoice received and queued for GRA processing",
    }
```

## Future Enhancements

1. **Task Prioritization**: Implement priority queues
2. **Dead Letter Queue**: Separate queue for failed tasks
3. **Task Scheduling**: Schedule submissions for later processing
4. **Batch Processing**: Process multiple submissions in batch
5. **Task Chaining**: Chain multiple tasks together
6. **Webhook Notifications**: Notify business on completion
7. **Analytics Dashboard**: Real-time task metrics
8. **Auto-scaling**: Automatically scale workers based on queue depth

## References

- [Celery Documentation](https://docs.celeryproject.io/)
- [Redis Documentation](https://redis.io/documentation)
- [GRA API Requirements](./requirements.md)
- [Submission Processor](./app/services/submission_processor.py)

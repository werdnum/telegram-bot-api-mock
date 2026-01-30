# Agent Guidelines

## Code Style

- Use type hints for all function parameters and return values
- Use Pydantic models for request/response bodies
- Prefer `async def` for all route handlers and services
- Use dependency injection via FastAPI's `Depends()`

## Testing

- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/`
- Use `pytest-asyncio` for async tests
- Use `pytest-httpx` for mocking HTTP requests (webhooks)

## API Conventions

- Bot API routes: `/bot{token}/{method}`
- Client API routes: `/client/{method}`
- All responses use `TelegramResponse[T]` wrapper with `ok` and `result` fields

## State Management

- All state is in-memory via `ServerState` singleton
- Use `get_state()` dependency to access state
- State modifications should use async locks

## Common Patterns

```python
# Route with state dependency
@router.post("/sendMessage")
async def send_message(
    request: SendMessageRequest,
    state: ServerState = Depends(get_state),
) -> TelegramResponse[Message]:
    ...

# Response format
return TelegramResponse(ok=True, result=message)
```

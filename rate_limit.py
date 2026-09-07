from fastapi import Request, HTTPException, status, Depends
from fastapi_limiter.depends import RateLimiter



# IDENTIFIER


async def get_user_id_identifier(request: Request) -> str:

    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    auth_header = request.headers.get("Authorization")

    if auth_header:
        return f"token:{auth_header}"

    return f"ip:{request.client.host}"


# CUSTOM CALLBACK


async def custom_callback(request: Request, response, pexpire: int):

    seconds_left = max(1, pexpire // 1000)

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "slow down!",
            "message": (
                f"You have exceeded your limit. "
                f"Please try again in {seconds_left} seconds."
            ),
            "retry_after_seconds": seconds_left
        }
    )



# RATE LIMIT LEVELS


strict_limit = Depends(
    RateLimiter(
        times=5,
        seconds=60,
        identifier=get_user_id_identifier,
        callback=custom_callback
    )
)


moderate_limit = Depends(
    RateLimiter(
        times=20,
        seconds=60,
        identifier=get_user_id_identifier,
        callback=custom_callback
    )
)


low_limit = Depends(
    RateLimiter(
        times=60,
        seconds=60,
        identifier=get_user_id_identifier,
        callback=custom_callback
    )
)

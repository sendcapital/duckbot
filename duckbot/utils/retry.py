import asyncio
from functools import wraps
from inspect import iscoroutinefunction
from utils import init_logger

logger = init_logger(__name__)


def retry(retry_count, initial_delay=2, backoff_factor=1.5):
  def decorator(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
      delay = initial_delay
      exception = None
      for time in range(retry_count):
        print('Try {}: {}'.format(func, time))
        try:
          return await func(*args, **kwargs)
        except Exception as exc:
          msg = "{}. Retry after {} seconds...".format(exc, delay)
          print(msg)
          await asyncio.sleep(delay)
          delay *= backoff_factor
          pass
      raise Exception('Exception after retry: {}'.format(exception))
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
      delay = initial_delay
      exception = None
      for time in range(retry_count):
        try:
          return func(*args, **kwargs)
        except Exception as exc:
          logger.error('Exception caught on iteration %d: %s', time, exc)
          pass
      raise Exception('Exception after retry: {}'.format(exception))

    if iscoroutinefunction(func):
        wrapper = async_wrapper
    else:
        wrapper = sync_wrapper
        
    return wrapper
  return decorator
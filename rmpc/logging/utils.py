import functools
import logging


logger = logging.getLogger(__name__)


def log_func_call(owner, fn, *args, **kwargs):
    fn_fqdn = getattr(fn, "__qualname__", None)
    if not fn_fqdn:
        owner_fqdn = getattr(owner, "__qualname__", str(owner))
        fn_fqdn = f"{owner_fqdn}.{fn}"

    logger.debug(
        "Called %s(%s%s%s)",
        fn_fqdn,
        ", ".join(f"{getattr(arg, '__qualname__', arg)!r}" for arg in list(args)),
        ", " if list(args) or kwargs else "",
        ", ".join(f"{k}={getattr(v, '__qualname__', v)!r}" for k, v in kwargs.items()),
    )


def wrap_call_log(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        log_func_call(
            args[0].__class__
            if len(args) >= 1 and hasattr(args[0], "__class__")
            else None,
            fn,
            *list(args)[1:],
            **kwargs,
        )
        return fn(*args, **kwargs)

    return wrapper

from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    """
    Tighter, dedicated rate limit for the login endpoint (see
    DEFAULT_THROTTLE_RATES['login'] in settings) so brute-forcing passwords
    is slow, without affecting the general per-user/per-anon limits that
    apply to every other endpoint.
    """
    scope = 'login'

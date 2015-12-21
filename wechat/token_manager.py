# encoding=utf-8

from datetime import datetime, timedelta
from time import sleep

import redis


class TokenManager(object):
    def get_token(self, fn_get_access_token):
        token = self.token
        expires = self.expires
        if not token and not expires:
            for i in xrang(12):
                sleep(5)
                if self.token:
                    break
        elif not token or expires and expires < datetime.now():
            self.expires = None
            self.refresh_token(fn_get_access_token)
        return self.token

    def refresh_token(self, fn_get_access_token):
        token, err = fn_get_access_token()
        if token and not err:
            self.token = token['access_token']
            self.expires = datetime.now() + \
                timedelta(seconds=token['expires_in'])
        else:
            self.token = None


class LocalTokenManager(TokenManager):
    def __init__(self):
        self._access_token = None
        self._expires = datetime.now()

    @property
    def token(self):
        return self._access_token

    @token.setter
    def token(self, token):
        self._access_token = token

    @property
    def expires(self):
        return self._expires

    @expires.setter
    def expires(self, expires):
        self._expires = expires


class RedisTokenManager(TokenManager):
    DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, postfix="", **kwargs):
        self.token_name = "_".join(["access_token", postfix])
        self.expires_name = "_".join(["access_token_expires", postfix])
        self.redis = redis.Redis(**kwargs)
        if not self.expires:
            self.expires = datetime.now()

    @property
    def token(self):
        token = self.redis.get(self.token_name)
        return str(token, "utf-8") if token and isinstance(
                token, bytes) else token

    @token.setter
    def token(self, token):
        self.redis.set(self.token_name, token)

    @property
    def expires(self):
        expires = self.redis.get(self.expires_name)
        return datetime.strptime(
                str(expires, "utf-8"),
                RedisTokenManager.DATETIME_FMT) if expires else None

    @expires.setter
    def expires(self, expires):
        self.redis.set(self.expires_name,
                       expires.strftime(RedisTokenManager.DATETIME_FMT)
                       if expires else None)

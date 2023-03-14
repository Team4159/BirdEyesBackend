import json
import os
import pathlib
import time
import typing
import urllib.parse
import flask

import requests
import werkzeug.datastructures


class CachingSession(requests.Session):
    def __init__(self, manual_cache: typing.Union[os.PathLike, str, None] = None) -> None:
        super().__init__()
        self.cache_path = pathlib.Path(manual_cache) if manual_cache else None
    
    def set_manual_cache(self, manual_cache: typing.Union[os.PathLike, str]):
        self.cache_path = pathlib.Path(manual_cache)
    
    def generate_response(self, data: bytes, code: int = 200):
        '''Generates a semi-fake requests response'''
        resp = requests.Response()
        resp.status_code = code
        resp._content = data
        return resp
    
    def get(self, url: str, cache_control: typing.Union[werkzeug.datastructures.RequestCacheControl, None] = None, **kwargs) -> requests.Response:
        parsed_url = urllib.parse.urlparse(url)
        if 'thebluealliance.com' not in parsed_url.netloc: #not BA
            return super().get(url, **kwargs)
        if not self.cache_path or not cache_control: #cache not enabled #DO NOT MERGE INTO THE TOP STATEMENT, IT IS SPLIT FOR READABILITY
            return super().get(url, **kwargs)
        path_list = parsed_url.path.split("/")[3:]
        cache_path = pathlib.Path(self.cache_path, *path_list[:-1], f"{path_list[-1]}.json")
        if cache_path.exists() and not cache_control.no_cache:
            cache_json = json.loads(cache_path.read_text())
            real_data = json.dumps(cache_json['data']).encode('utf8')
            if 'last-update' in cache_json and (cache_control.max_age is None or time.time() - cache_json['last-update'] <= cache_control.max_age):
                return self.generate_response(real_data, code=cache_json['code'] if 'code' in cache_json else 200)
            #if the response isn't new enough let the if-statement fall back to manually requesting and caching
        resp = super().get(url, **kwargs)
        if cache_control.no_store or not self.cache_path.is_dir():
            return resp
        cached_data = {
            "last-update": time.time(),
            "code": resp.status_code,
            "data": resp.json()
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cached_data))
        return resp

session = CachingSession() #SHOULD REALLY BE A CONTEXT-SENSITIVE VARIABLE BUT WHATEVER

def get_with_cache(url: str):
    return session.get(url, cache_control=flask.request.cache_control)

from django.core.cache import cache
import hashlib
import json


def make_key(prefix, text):
    raw = f"{prefix}:{text}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached_embedding(query):
    key = make_key("embed", query)
    return cache.get(key)


def set_cached_embedding(query, vector):
    key = make_key("embed", query)
    cache.set(key, vector, timeout=86400)


def get_cached_answer(query):
    key = make_key("answer", query)
    return cache.get(key)


def set_cached_answer(query, data):
    key = make_key("answer", query)
    cache.set(key, data, timeout=86400)

def get_or_create_embedding(query, embeddings):
    cached = get_cached_embedding(query)

    if cached:
        return cached

    vector = embeddings.embed_query(query)

    set_cached_embedding(query, vector)

    return vector
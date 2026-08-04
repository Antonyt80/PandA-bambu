"""Negotiation classifies validated offers without interpreting payloads."""
from .envelopes import NegotiationOffer,NegotiationResult
from .errors import NegotiationError
from .registry import SchemaKey
def _offer(offer):
    if isinstance(offer,NegotiationOffer):return offer
    try:return NegotiationOffer.from_dict(offer)
    except Exception as error:raise NegotiationError(getattr(error,"code","malformed-offer")) from None
def negotiate(registry,offer):
    if not getattr(registry,"frozen",False):raise NegotiationError("registry-not-frozen")
    offer=_offer(offer)
    if offer.namespace not in registry.namespaces:raise NegotiationError("unknown-namespace")
    if offer.profile not in registry.profiles:raise NegotiationError("unknown-profile")
    for extension in offer.extensions:
        registered=registry.extensions.get(extension.name)
        if registered is None:
            if extension.required or not extension.preservable or not registry.preserve_unknown_optional_extensions:raise NegotiationError("unknown-extension")
        elif extension.preservable != registered:
            raise NegotiationError("malformed-extension")
    key=SchemaKey(offer.namespace,offer.schema,offer.version,offer.profile)
    if key in registry.schemas:return NegotiationResult("exact-compatible")
    candidates=sorted((entry for entry in registry.migrations if entry.source==key and entry.target in registry.schemas and entry.lossless),key=lambda x:x.operation)
    if len(candidates)==1:return NegotiationResult("migration-required","migration-required",candidates[0].operation)
    if len(candidates)>1:raise NegotiationError("ambiguous-migration")
    if any(schema.namespace==offer.namespace and schema.schema==offer.schema for schema in registry.schemas):raise NegotiationError("unknown-version")
    raise NegotiationError("unknown-schema")
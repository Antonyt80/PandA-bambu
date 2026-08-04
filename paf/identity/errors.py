"""Stable failures for the PAF R1 identity profile."""
class IdentityError(ValueError):
    def __init__(self, code, message=None): self.code=code; super().__init__(message or code)
class IdentitySyntaxError(IdentityError): pass
class CanonicalizationError(IdentityError): pass
class DigestError(IdentityError): pass
class RegistryError(IdentityError): pass
class NegotiationError(IdentityError): pass
class ExtensionError(IdentityError): pass
class MigrationError(IdentityError): pass

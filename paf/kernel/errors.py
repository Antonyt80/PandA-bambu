"""Stable failures for the PAF v11 common-model slice."""
class PafModelError(ValueError):
    def __init__(self, code, message=None): self.code=code; super().__init__(message or code)
class RecordError(PafModelError): pass
class ModelError(PafModelError): pass
class RefinementError(PafModelError): pass
class ProjectionError(PafModelError): pass
class WorkGraphError(PafModelError): pass
class ActivationError(WorkGraphError): pass

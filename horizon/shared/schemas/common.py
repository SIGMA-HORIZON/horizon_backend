"""Schémas transverses (messages, erreurs HTTP)."""

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str = Field(..., description="Message informatif")


class ErrorDetail(BaseModel):
    detail: str = Field(..., description="Détail de l'erreur")

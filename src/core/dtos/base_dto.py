"""
Moduł z bazową klasą DTO.

Zawiera klasę BaseDTO służącą jako podstawę
dla wszystkich Data Transfer Objects w aplikacji.
"""

from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """
    Bazowa klasa dla wszystkich Data Transfer Objects.
    
    Zapewnia standardową konfigurację Pydantic dla wszystkich DTO
    w aplikacji, w tym obsługę atrybutów z modeli ORM.
    """
    model_config = ConfigDict(from_attributes=True)

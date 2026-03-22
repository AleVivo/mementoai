from datetime import datetime
from typing import Annotated, Any, Literal, Optional, Union
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Blocchi primitivi — usati dentro SchemaField
# ---------------------------------------------------------------------------

class SelectOption(BaseModel):
    """
    Singola opzione di un campo select.
    { "value": "ollama", "label": "Ollama" }
    """
    value: str
    label: str

class DependsOn(BaseModel):
    """
    Le opzioni disponibili dipendono dal valore di un altro campo.
    
    Esempio: il campo "model" dipende da "provider".
    Se provider = "ollama" → mostra i modelli Ollama.
    Se provider = "openai" → mostra i modelli OpenAI.
    
    {
      "field": "provider",
      "options": {
        "ollama": [{"value": "qwen2.5:7b", "label": "Qwen 2.5 7B"}],
        "openai": [{"value": "gpt-4o",     "label": "GPT-4o"}]
      }
    }
    """
    field: str
    options: dict[str, list[SelectOption]]

class RequiredIf(BaseModel):
    """
    Il campo diventa obbligatorio solo se un altro campo soddisfa la condizione.
    Usa "in" o "not_in" — mai entrambi sullo stesso oggetto.

    Esempio: api_key è obbligatoria se provider NON è ollama.
    { "field": "provider", "not_in": ["ollama"] }

    Esempio: host è obbligatorio se provider È ollama.
    { "field": "provider", "in": ["ollama"] }
    """
    field: str
    in_: Optional[list[str]] = Field(default=None, alias="in")
    not_in: Optional[list[str]] = None

    model_config = {
        "populate_by_name": True,
    }

# ---------------------------------------------------------------------------
# SchemaField — discriminated union sul campo "type"
# ---------------------------------------------------------------------------

class _BaseField(BaseModel):
    key: str
    label: str
    required: bool = False
    required_if: Optional[RequiredIf] = None

class ToggleField(_BaseField):
    type: Literal["toggle"]
    
class TextField(_BaseField):
    type: Literal["text"]
    placeholder: Optional[str] = None

class SecretField(_BaseField):
    type: Literal["secret"]
    placeholder: Optional[str] = None

class SelectField(_BaseField):
    type: Literal["select"]
    options: Optional[list[SelectOption]] = None
    depends_on: Optional[DependsOn] = None
    required: bool = False    


ConfigSchemaField = Annotated[
    Union[TextField, SecretField, SelectField, ToggleField],
    Field(discriminator="type")
]


# ---------------------------------------------------------------------------
# ConfigSchema — documento config_schema in MongoDB
# ---------------------------------------------------------------------------

class ConfigSchema(BaseModel):
    id: str = Field(alias="_id")
    type: Literal["integration", "settings"]
    label: str
    description: Optional[str] = None
    fields: list[ConfigSchemaField]

    model_config = {"populate_by_name": True}

# ---------------------------------------------------------------------------
# ConfigValues — documento config_values in MongoDB
# ---------------------------------------------------------------------------

class ConfigValues(BaseModel):
    id: str = Field(alias="_id")
    values: dict[str, Any]
    status: Optional[Literal["unknown", "active", "error"]] = "unknown"
    status_message: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }

# ---------------------------------------------------------------------------
# SchemaFieldWithValue — field dello schema arricchito con il valore corrente
# Usato solo nelle response verso il frontend — non viene mai salvato
# ---------------------------------------------------------------------------

class TextFieldWithValue(TextField):
    value: Optional[str] = None


class SecretFieldWithValue(SecretField):
    value: Optional[str] = None


class SelectFieldWithValue(SelectField):
    value: Optional[str] = None


class ToggleFieldWithValue(ToggleField):
    value: bool = False


SchemaFieldWithValue = Annotated[
    Union[
        TextFieldWithValue,
        SecretFieldWithValue,
        SelectFieldWithValue,
        ToggleFieldWithValue,
    ],
    Field(discriminator="type")
]


# ---------------------------------------------------------------------------
# ConfigSectionResponse — quello che il frontend riceve
# Schema + values merged, secrets mascherati
# ---------------------------------------------------------------------------
class ConfigSectionResponse(BaseModel):
    """
    Response del GET /admin/config e GET /admin/config/{section_id}.
    È il merge di ConfigSchema + ConfigValues.
    Non corrisponde a nessun documento MongoDB — viene costruito server-side.
    """
    id: str
    type: Literal["integration", "settings"]
    label: str
    description: Optional[str] = None
    fields: list[SchemaFieldWithValue]
    status: Optional[Literal["unknown", "active", "error"]] = None
    status_message: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


# ---------------------------------------------------------------------------
# ConfigUpdateRequest — body del PUT /admin/config/{section_id}
# ---------------------------------------------------------------------------

class ConfigUpdateRequest(BaseModel):
    """
    Body della PUT /admin/config/{section_id}.
    L'admin manda tutti i valori della sezione — non un patch parziale.
    La validazione contro lo schema avviene nel service, non qui.
    
    Usiamo dict[str, Any] perché i campi variano per sezione —
    non possiamo tipizzarli staticamente senza conoscere la sezione.
    """
    values: dict[str, Any]
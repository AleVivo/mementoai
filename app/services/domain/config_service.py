"""
Service per la gestione della configurazione admin.

Responsabilità:
- Merge schema + values → ConfigSectionResponse
- Validazione values ricevuti contro lo schema
- Cifratura/decifratura campi secret (delega a utils.encryption)
- Salvataggio tramite config_repository
"""

import logging
from typing import Any, Dict, Optional
from app.db.repositories import config_repository
from app.models import config
from app.utils import encryption

logger = logging.getLogger(__name__)

def _build_field_with_value(
    field_schema: config.ConfigSchemaField,
    field_values: Optional[Dict],
    decrypt_secrets: bool = False
) -> config.SchemaFieldWithValue:
    """
    Arricchisce un field dello schema con il valore corrente.

    decrypt_secrets=True viene usato solo da get_decrypted_values —
    mai nelle response HTTP. Restituisce il valore in chiaro per i secret.
    decrypt_secrets=False (default) maschera i secret con "***".
    """
    raw_value = field_values.get(field_schema.key) if field_values else None

    if isinstance(field_schema, config.TextField):
        return config.TextFieldWithValue(**field_schema.model_dump(), value=raw_value)
    
    elif isinstance(field_schema, config.SecretField):
        if raw_value is None:
            display = None
        elif decrypt_secrets:
            display = encryption.decrypt(raw_value)
        else:
            display = encryption.mask_secret(raw_value)
        return config.SecretFieldWithValue(**field_schema.model_dump(), value=display)

    elif isinstance(field_schema, config.SelectField):
        return config.SelectFieldWithValue(**field_schema.model_dump(), value=raw_value)
    
    elif isinstance(field_schema, config.ToggleField):
        return config.ToggleFieldWithValue(**field_schema.model_dump(), value=raw_value or False)
    
    else:
        raise ValueError(f"Tipo di field non gestito: {type(field_schema)}")
    
def _merge_to_response(
    config_schema: config.ConfigSchema,
    config_values: Optional[config.ConfigValues],
    decrypt_secrets: bool = False,
) -> config.ConfigSectionResponse:
    """
    Merge di schema + values in un ConfigSectionResponse.
    """
    values_dict = config_values.values if config_values else None

    fields_with_value = [
        _build_field_with_value(field, values_dict, decrypt_secrets=decrypt_secrets)
        for field in config_schema.fields
    ]

    return config.ConfigSectionResponse(
        id=config_schema.id,
        type=config_schema.type,
        label=config_schema.label,
        description=config_schema.description,
        fields=fields_with_value,
        status=config_values.status if config_values else None,
        status_message=config_values.status_message if config_values else None,
        last_tested_at=config_values.last_tested_at if config_values else None,
        updated_at=config_values.updated_at if config_values else None,
        updated_by=config_values.updated_by if config_values else None,
    )

# ---------------------------------------------------------------------------
# Validazione
# ---------------------------------------------------------------------------

def _is_field_required_by_condition(
    required_if: Optional[config.RequiredIf],
    incoming: dict[str, Any],
) -> bool:
    """
    Restituisce True se il campo è obbligatorio dati i values in arrivo.
    """
    if required_if is None:
        return False

    ref_value = incoming.get(required_if.field)

    if required_if.in_ is not None:
        return ref_value in required_if.in_

    if required_if.not_in is not None:
        return ref_value not in required_if.not_in

    return False


def _resolve_valid_options(
    field: config.SelectField,
    incoming: dict[str, Any],
) -> Optional[list[str]]:
    """
    Restituisce i valori validi per un SelectField.
    None se non è possibile determinarli.
    """
    if field.options:
        return [opt.value for opt in field.options]

    if field.depends_on:
        ref_value = incoming.get(field.depends_on.field)
        if ref_value is None:
            return None
        options_for_value = field.depends_on.options.get(ref_value, [])
        return [opt.value for opt in options_for_value]

    return None


def _validate_values(
    schema: config.ConfigSchema,
    incoming: dict[str, Any],
) -> list[str]:
    """
    Valida i values ricevuti contro lo schema.
    Restituisce lista errori — vuota se tutto è valido.
    """
    errors: list[str] = []

    for field in schema.fields:
        value = incoming.get(field.key)
        is_empty = value is None or value == ""

        if field.required and is_empty:
            errors.append(f"Campo '{field.label}' è obbligatorio.")
            continue

        if _is_field_required_by_condition(field.required_if, incoming) and is_empty:
            errors.append(
                f"Campo '{field.label}' è obbligatorio "
                f"con la configurazione selezionata."
            )
            continue

        if isinstance(field, config.SelectField) and value is not None:
            valid_options = _resolve_valid_options(field, incoming)
            if valid_options is not None and value not in valid_options:
                errors.append(
                    f"Valore '{value}' non valido per '{field.label}'. "
                    f"Opzioni valide: {', '.join(valid_options)}."
                )

    return errors

# ---------------------------------------------------------------------------
# Funzioni pubbliche del service
# ---------------------------------------------------------------------------

async def get_all_config() -> list[config.ConfigSectionResponse]:
    """
    Tutte le sezioni con schema + values merged.
    Usato da GET /admin/config.
    """
    schemas_raw = await config_repository.get_all_schemas()
    values_raw = await config_repository.get_all_values()

    values_by_id: dict[str, config.ConfigValues] = {}
    for v in values_raw:
        try:
            values_by_id[v["_id"]] = config.ConfigValues.model_validate(v)
        except Exception:
            logger.warning(f"[config_service] config_values malformato: _id={v.get('_id')}")

    result = []
    for s in schemas_raw:
        try:
            schema = config.ConfigSchema.model_validate(s)
            cv = values_by_id.get(schema.id)
            result.append(_merge_to_response(schema, cv))
        except Exception:
            logger.warning(f"[config_service] config_schema malformato: _id={s.get('_id')}")

    return result

async def get_config_section(section_id: str) -> Optional[config.ConfigSectionResponse]:
    """
    Singola sezione con schema + values merged.
    Restituisce None se la sezione non esiste in config_schema.
    Usato da GET /admin/config/{section_id}.
    """
    schema_raw = await config_repository.get_schema(section_id)
    if schema_raw is None:
        return None

    schema = config.ConfigSchema.model_validate(schema_raw)
    values_raw = await config_repository.get_values(section_id)
    cv = config.ConfigValues.model_validate(values_raw) if values_raw else None

    return _merge_to_response(schema, cv)

async def update_config_section(
    section_id: str,
    incoming: dict[str, Any],
    updated_by: str,
) -> tuple[Optional[config.ConfigSectionResponse], list[str]]:
    """
    Valida e salva i values per una sezione.
    Restituisce (response, errors).

    Se errors è non vuoto il salvataggio non avviene.
    Il router risponde 422 con la lista errori.
    Usato da PUT /admin/config/{section_id}.
    """
    schema_raw = await config_repository.get_schema(section_id)
    if schema_raw is None:
        return None, []

    schema = config.ConfigSchema.model_validate(schema_raw)

    errors = _validate_values(schema, incoming)
    if errors:
        return None, errors

    # Cifra i campi secret prima di salvare
    # "***" significa che l'admin non ha modificato il secret —
    # manteniamo il valore cifrato già in DB
    values_to_save: dict[str, Any] = {}
    for field in schema.fields:
        value = incoming.get(field.key)
        if isinstance(field, config.SecretField) and value is not None and value != "***":
            values_to_save[field.key] = encryption.encrypt(value)
        else:
            values_to_save[field.key] = value

    values_raw = await config_repository.upsert_values(section_id, values_to_save, updated_by)
    cv = config.ConfigValues.model_validate(values_raw)

    return _merge_to_response(schema, cv), []


async def get_decrypted_values(section_id: str) -> Optional[dict[str, Any]]:
    """
    Restituisce i values con i secret decifrati.
    Usato SOLO dagli handler reload dei provider — mai negli endpoint HTTP.
    """
    schema_raw = await config_repository.get_schema(section_id)
    if schema_raw is None:
        return None

    values_raw = await config_repository.get_values(section_id)
    if values_raw is None:
        return None

    schema = config.ConfigSchema.model_validate(schema_raw)
    cv = config.ConfigValues.model_validate(values_raw)

    merged = _merge_to_response(schema, cv, decrypt_secrets=True)

    return {
        field.key: field.value  # type: ignore[union-attr]
        for field in merged.fields
    }
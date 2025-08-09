from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ConfigModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",  # Disallow extra fields
        populate_by_name=True,  # Allow population by field name
        use_enum_values=True,  # Use enum values directly
        alias_generator=to_camel,  # Convert field names to camelCase
        from_attributes=True,
    )

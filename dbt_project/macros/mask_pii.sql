-- macros/mask_pii.sql
-- Macro to mask PII fields in query outputs

{% macro mask_email(email_column) %}
    concat(
        substring({{ email_column }}, 1, 2),
        '***@',
        split_part({{ email_column }}, '@', 2)
    )
{% endmacro %}

{% macro mask_phone(phone_column) %}
    concat(
        substring({{ phone_column }}, 1, 3),
        '****',
        right({{ phone_column }}, 2)
    )
{% endmacro %}

{% macro mask_national_id(id_column) %}
    concat(
        substring({{ id_column }}, 1, 2),
        '-****-****'
    )
{% endmacro %}

{% macro mask_name(name_column) %}
    concat(
        split_part({{ name_column }}, ' ', 1),
        ' ***'
    )
{% endmacro %}

-- Comprehensive PII masking macro
{% macro mask_customer_pii() %}
    {{ mask_name('full_name') }} as full_name_masked,
    {{ mask_email('email') }} as email_masked,
    {{ mask_phone('phone') }} as phone_masked,
    {{ mask_national_id('national_id') }} as national_id_masked
{% endmacro %}
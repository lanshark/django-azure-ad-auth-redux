import logging
import requests
from base64 import b64decode
from urllib.parse import urlencode

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate
from django.conf import settings
from lxml import etree

logger = logging.getLogger("azure_ad_auth")


AUTHORITY = getattr(settings, "AAD_AUTHORITY", "https://login.microsoftonline.com")
SCOPE = getattr(settings, "AAD_SCOPE", "openid")
RESPONSE_TYPE = getattr(settings, "AAD_RESPONSE_TYPE", "id_token")
RESPONSE_MODE = getattr(settings, "AAD_RESPONSE_MODE", "form_post")
TENANT_ID = settings.AAD_TENANT_ID
CLIENT_ID = settings.AAD_CLIENT_ID
ALWAYS_AUTHENTICATE = getattr(settings, "AAD_ALWAYS_AUTHENTICATE", True)


def get_login_url(
    authority=AUTHORITY,
    response_type=RESPONSE_TYPE,
    response_mode=RESPONSE_MODE,
    scope=SCOPE,
    client_id=CLIENT_ID,
    redirect_uri=None,
    nonce=None,
    state=None,
    always_authenticate=ALWAYS_AUTHENTICATE,
):
    param_dict = {
        "response_type": response_type,
        "response_mode": response_mode,
        "scope": scope,
        "client_id": client_id,
    }
    if redirect_uri is not None:
        param_dict["redirect_uri"] = redirect_uri
    if nonce is not None:
        param_dict["nonce"] = nonce
    if state is not None:
        param_dict["state"] = state
    if always_authenticate:
        param_dict["prompt"] = "login"
    params = urlencode(param_dict)
    return f"{authority}/common/oauth2/authorize?{params}"


def get_logout_url(redirect_uri, authority=AUTHORITY):
    params = urlencode(
        {
            "post_logout_redirect_uri": redirect_uri,
        },
    )
    return f"{authority}/common/oauth2/logout?{params}"


def get_federation_metadata_document_url(authority=AUTHORITY, tenant_id=TENANT_ID):
    return f"{authority}/{tenant_id}/federationmetadata/2007-06/federationmetadata.xml"


def parse_x509_der_list(federation_metadata_document):
    document = etree.fromstring(federation_metadata_document)  # noqa: S320
    certificate_elems = document.findall(
        ".//{http://www.w3.org/2000/09/xmldsig#}X509Certificate",
    )
    b64encoded_ders = {certificate_elem.text for certificate_elem in certificate_elems}
    return [b64decode(b64encoded_der) for b64encoded_der in b64encoded_ders]


def get_public_keys():
    try:
        federation_metadata_document_url = get_federation_metadata_document_url()
        response = requests.get(federation_metadata_document_url)  # noqa: S113
        if not response.ok:
            raise
        response.encoding = response.apparent_encoding
        x509_der_list = parse_x509_der_list(response.text.encode("utf-8"))
        keys = [
            load_der_x509_certificate(
                x509_der,
                default_backend(),
            ).public_key()
            for x509_der in x509_der_list
        ]
    except Exception:  # TODO - which ones exactly?
        keys = []
    return keys


def get_token_payload(token=None, audience=CLIENT_ID, nonce=None):
    headers = jwt.get_unverified_header(token)
    algorithm = headers.get("alg", "RS256")
    for key in get_public_keys():
        try:
            payload = jwt.decode(
                token,
                key=key,
                audience=audience,
                algorithms=[algorithm],
            )

            if payload["nonce"] != nonce:
                continue

            return payload
        except (jwt.InvalidTokenError, IndexError) as e:
            logger.error(f"InvalidTokenError: {e!s}")
            pass

    return None


def get_token_payload_email(payload, field_name="upn"):
    return get_token_payload_field(payload, field_name)


def get_token_payload_field(payload, field_name, def_value=None):
    return payload[field_name] if payload and field_name in payload else def_value

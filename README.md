# Digital signing service

A service providing Kaleidos the functionality for digitally signing documents. 

## Configuration

- `SIGNINGHUB_API_URL`: Base-URL of the Signinghub-API

API-client identification at SigningHub. For more info, see the SigningHub user-manual on [managing third party integrations](https://manuals.ascertia.com/SigningHubv7/default.aspx#pageid=1111).
- `SIGNINGHUB_CLIENT_ID`
- `SIGNINGHUB_CLIENT_SECRET`

Authentication at VO-network, through SSL client certificate authentication
- `CERT_FILE_PATH`: Path to client certificate file (`.pem`-format)
- `KEY_FILE_PATH`: Path to client private key file

Credentials of the Kaleidos machine user at SigningHub
- `SIGNINGHUB_MACHINE_ACCOUNT_USERNAME`
- `SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD`

## REST API

The available API-endpoints are documented in an [OpenAPI v3](http://spec.openapis.org/oas/v3.0.3) spec-file `openapi.yaml`.

## Used models

#### Concepts

- Signing subcase type: `"http://kanselarij.vo.data.gift/id/concept/procedurestap-types/fd98c5d0-a218-4fbe-a4d3-029c79aea5c5`
- Signing preparation activity type: `http://kanselarij.vo.data.gift/id/concept/activiteit-types/001d38fb-b285-41ef-a252-4e70208e9266`
- Signing activity type: `http://mu.semte.ch/vocabularies/ext/publicatie/Handtekenactiviteit`
- Signing "wrap-up" type (receiving the final signed document): `http://kanselarij.vo.data.gift/id/concept/activiteit-types/d05978cb-3219-4ed4-9ab5-45b03c58a0ae`

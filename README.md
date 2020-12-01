# Digital signing service

A service providing Kaleidos the functionality for digitally signing documents. 

## Configuration

- `SIGNINGHUB_API_URL`: Base-URL of the Signinghub-API

API-client identification at SigningHub. For more info, see the SigningHub user-manual on [managing third party integrations](https://manuals.ascertia.com/SigningHubv7/default.aspx#pageid=1111).
- `SIGNINGHUB_CLIENT_ID`: API client-id
- `SIGNINGHUB_CLIENT_SECRET`: Base-URL of the Signinghub-API

Authentication at VO-network, through SSL client certificate authentication
- `CERT_FILE_PATH`: Path to client certificate file (`.pem`-format)
- `KEY_FILE_PATH`: Path to client private key file

Credentials of the Kaleidos machine user at SigningHub
- `SIGNINGHUB_MACHINE_ACCOUNT_USERNAME`
- `SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD`

### REST API

The available API-endpoints are documented in an [OpenAPI v3](http://spec.openapis.org/oas/v3.0.3) spec-file `openapi.yaml`.

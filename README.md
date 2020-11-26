# Digital signing service

A service providing Kaleidos the functionality for digitally signing documents. 

## Configuration

- `SIGNINGHUB_API_URL`: Base-URL of the Signinghub-API
- `CERT_FILE_PATH`: Path to client certificate file (`.pem`-format)
- `KEY_FILE_PATH`: Path to client private key file


### REST API

The available API-endpoints are documented in an [OpenAPI v3](http://spec.openapis.org/oas/v3.0.3) spec-file `openapi.yaml`.

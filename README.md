# Digital signing service

A service providing Kaleidos the functionality for digitally signing documents. 

## Configuration

- `SIGNINGHUB_API_URL`: Base-URL of the Signinghub-API
- `SIGNINGHUB_IFRAME_REDIRECT_URL`: URL-path to redirect to when finishing Iframe interaction. Note that a default for this is configurable in SigningHub integration settings too, but for development purposes it's useful to be able to configure per environment.

API-client identification at SigningHub. For more info, see the SigningHub user-manual on [managing third party integrations](https://manuals.ascertia.com/SigningHubv7/Managethirdpartyintegrations.html).
- `SIGNINGHUB_CLIENT_ID`
- `SIGNINGHUB_CLIENT_SECRET`

Authentication at VO-network, through SSL client certificate authentication
- `CERT_FILE_PATH`: Path to client certificate file (`.pem`-format)
- `KEY_FILE_PATH`: Path to client private key file

_Note that both of above parameters must be set to activate client certificate authentication. If omitted, no client cert. auth. will be attempted._

Credentials of the Kaleidos machine user at SigningHub
- `SIGNINGHUB_MACHINE_ACCOUNT_USERNAME`
- `SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD`


#### docker-compose snippet

```yml
  digital-signing:
    image: kanselarij/digital-signing # Make sure to specify a tagged version here
    environment:
      SIGNINGHUB_API_URL: ""
      SIGNINGHUB_IFRAME_REDIRECT_URL: ""
      SIGNINGHUB_CLIENT_ID: ""
      SIGNINGHUB_CLIENT_SECRET: ""
      CERT_FILE_PATH: ""
      KEY_FILE_PATH: ""
      SIGNINGHUB_MACHINE_ACCOUNT_USERNAME: ""
      SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD: ""
    volumes:
      -./data/files:/share
      -./config/digital-signing/cert:/cert
    restart: always
```

## REST API

The available API-endpoints are documented in an [OpenAPI v3](http://spec.openapis.org/oas/v3.0.3) spec-file `openapi.yaml`.

## Used models

Read the Kaleidos documentation regarding the [digital signing data model](https://github.com/kanselarij-vlaanderen/kaleidos-documentation/blob/master/data-model/signing-flow.md).
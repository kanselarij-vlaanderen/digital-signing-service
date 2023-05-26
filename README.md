# Digital signing service

A service providing Kaleidos the functionality for digitally signing documents.

## Configuration

VO's SigningHub instance compartmentalizes users per organization (OVO-code) as separate "enterprises". Impersonating an organization user can only be done through a machine user that is within the same organization as the user to impersonate. Thus, since the target audience of the digital signing service spans multiple VO organizations, we also need to be able to configure multiple machine users for API-client identification at SigningHub. This is done by mounting a python source file to `/app/authentication_config.py`. Check out the config file included in the repo for more details.

For more details on SigningHub API authentication, see ["managing third party integrations"](https://manuals.ascertia.com/SigningHubv7/Managethirdpartyintegrations.html) in their manual.

- `SIGNINGHUB_API_URL`: Base-URL of the Signinghub-API
- `SIGNINGHUB_IFRAME_REDIRECT_URL`: URL-path to redirect to when finishing Iframe interaction. Note that a default for this is configurable in SigningHub integration settings too, but for development purposes it's useful to be able to configure per environment.


Authentication at VO-network, through SSL client certificate authentication
- `CERT_FILE_PATH`: Path to client certificate file (`.pem`-format)
- `KEY_FILE_PATH`: Path to client private key file

_Note that both of above parameters must be set to activate client certificate authentication. If omitted, no client cert. auth. will be attempted._

- `SYNC_CRON_PATTERN`: Cronjob pattern that will be used to periodically sync all ongoing sign flows (default: `*/2 * * * *`)


#### docker-compose snippet

```yml
  digital-signing:
    image: kanselarij/digital-signing # Make sure to specify a tagged version here
    environment:
      SIGNINGHUB_API_URL: ""
      SIGNINGHUB_IFRAME_REDIRECT_URL: ""
      CERT_FILE_PATH: ""
      KEY_FILE_PATH: ""
    volumes:
      - ./data/files:/share
      - ./config/digital-signing/cert:/cert:ro
      - ./config/digital-signing/authentication.py:/app/authentication_config.py:ro
    restart: always
```

## REST API

The available API-endpoints are documented in an [OpenAPI v3](http://spec.openapis.org/oas/v3.0.3) spec-file `openapi.yaml`.

## Used models

Read the Kaleidos documentation regarding the [digital signing data model](https://github.com/kanselarij-vlaanderen/kaleidos-documentation/blob/master/data-model/signing-flow.md).

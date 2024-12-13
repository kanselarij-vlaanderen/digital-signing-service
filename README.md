# Digital signing service

A service providing Kaleidos the functionality for digitally signing documents.

## Configuration

VO's SigningHub instance compartmentalizes users per organization (OVO-code) as separate "enterprises". Impersonating an organization user can only be done through a machine user that is within the same organization as the user to impersonate. Thus, since the target audience of the digital signing service spans multiple VO organizations, we also need to be able to configure multiple machine users for API-client identification at SigningHub. This is done by mounting a python source file to `/app/authentication_config.py`. Check out the config file included in the repo for more details.

For more details on SigningHub API authentication, see ["managing third party integrations"](https://manuals.ascertia.com/SigningHubv7/Managethirdpartyintegrations.html) in their manual.

- `SIGNINGHUB_API_URL`: Base-URL of the Signinghub-API

Authentication at VO-network, through SSL client certificate authentication
- `CERT_FILE_PATH`: Path to client certificate file (`.pem`-format)
- `KEY_FILE_PATH`: Path to client private key file

_Note that both of above parameters must be set to activate client certificate authentication. If omitted, no client cert. auth. will be attempted._

- `SIGNINGHUB_APP_DOMAIN`: Signinghub web-app domain. Used for generating links to the web-app
- `SYNC_CRON_PATTERN`: Cronjob pattern that will be used to periodically sync all ongoing sign flows (default: `*/2 * * * *`)

Autoplacing signatures
- `ADD_SIGNATURE_FIELD_ENABLED`: place a signature field on the signers name for decision reports (default: `false`)
- `SIGNATURE_FIELD_WIDTH`: width for the autoplace field (default 100)
- `SIGNATURE_FIELD_HEIGHT`: height for the autoplace field (default 40)

#### docker-compose snippet

```yml
  digital-signing:
    image: kanselarij/digital-signing # Make sure to specify a tagged version here
    environment:
      SIGNINGHUB_API_URL: ""
      SIGNINGHUB_APP_DOMAIN: ""
      CERT_FILE_PATH: ""
      KEY_FILE_PATH: ""
      ACCOUNT_GRAPH: "http://mu.semte.ch/graphs/system/users"
      SYNC_CRON_PATTERN: "*/2 * * * *"
      ADD_SIGNATURE_FIELD_ENABLED: true
      SIGNATURE_FIELD_WIDTH: 100
      SIGNATURE_FIELD_HEIGHT: 40
    volumes:
      - ./data/files:/share
      - ./config/digital-signing/cert:/cert:ro
      - ./config/digital-signing/authentication.py:/app/authentication_config.py:ro
    restart: always
```

## Used models

Read the Kaleidos documentation regarding the [digital signing data model](https://github.com/kanselarij-vlaanderen/kaleidos-documentation/blob/master/data-model/signing-flow.md).

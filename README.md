# Server Monitoring (for gameservers)

## Installation
We need docker, docker-compose and git installed on your system.
- `git clone https://github.com/element-code/server-monitoring.git`
- `cd server-monitoring`
- `git fetch --tags`
- `git checkout $(git tag -l --contains HEAD | tail -n1)`
- `cp config.example.yml config.yml`
- Edit the `config.yml` file to your needs, see [configuration](#configuration).
- `cp example.env .env`
- Edit the `.env` file to your needs, see [configuration](#configuration).
- `docker compose up --detach --build`

## Configuration
When you change the configuration, you need to restart the containers:
- `docker-compose down`
- `docker-compose up -d --build`

### Defaults
In the `.env` set some defaults:
- Set your Timezone: `TZ=Europe/Berlin`

### Exposure to the network
In the `.env` you can configure network binding:
- `GRAFANA_PORT` is the port the ui will be exposed on (website, non-ssl!). Use a reverse-proxy for ssl-termination.
- `GRAFANA_BIND_ADDRESS` is usually localhost, change it to `0.0.0.0` to expose it to the network. You shouldn't do this on public hosts. Use some reverse-proxy instead.

### Servers
In the `config.yml` file, you can add your gameservers under the `servers:` section.
Each Server can contain the following parameters:
- `hostname` FQDN or IP address of the server
- `resolvers` A list of resolvers to use for data-collection, see `/data-collector/src/resolver/resolvers`

Each Resolver can get its own configuration, see respective resolver. An example is state below for the `hll-crcon` resolver
Basic network resolvers are automatically applied.

All values can be set using environment variables in the `.env` file.
```yaml
servers:
  - hostname: ${SERVER_1_HOSTNAME}
    resolvers:
      hll-crcon:
        api_key: ${RESOLVER_HLL_CRCON_1_API_KEY}
        base_url: ${RESOLVER_HLL_CRCON_1_BASE_URL}

  - hostname: ${SERVER_2_HOSTNAME}
```

#### Debugging
If something doesn't work as expected, give it a few minutes to resolve.
- Did you restart the containers after changing the configuration?
- Check the logs of the data-collector: `docker logs server-monitoring_data-collector`

### Authentication

#### Anonymous Viewing
You can enable anonymous viewing by setting the following environment variable in the `.env` file.
This will allow **everyone** to view the dashboards without authentication.
Use only for non-public hosts or behind authentication-proxies.
- `GRAFANA_ANONYMOUS_ENABLED=true`

#### Admin
You usually don't need the admin account if you use discord or anonymous viewing.
You can enable admin-viewing by setting the following environment variables in the `.env` file.
```env
GRAFANA_DISABLE_ADMIN=false
GRAFANA_ADMIN_USER=admin
# change this to something secure!
# no $, }, ' or " characters allowed!
GRAFANA_ADMIN_PASSWORD=qC-1-h5m15jq;ttC6pr6LP9GaF8U#,F
```

## Updates
- `docker-compose down`
- `git fetch --tags`
- `git checkout $(git tag -l --contains HEAD | tail -n1)`
- `docker-compose up -d --build`

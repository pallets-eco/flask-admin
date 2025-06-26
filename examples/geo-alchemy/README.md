# GeoAlchemy Example

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/geo-alchemy
```

<!-- TODO: Let's automate the steps down below as part of main.py and the testcontainer we use so that manually nothing needs to happen? -->

Open the PostgreSQL Interactive terminal by running `psql postgres` command and create a database and user for the example:

```sql
CREATE DATABASE flask_admin_geo;
CREATE ROLE flask_admin_geo LOGIN PASSWORD 'flask_admin_geo';
GRANT ALL PRIVILEGES ON DATABASE flask_admin_geo TO flask_admin_geo;
```

Then, create the `postgis` extension in the database:

```shell
psql -d flask_admin_geo -c "CREATE EXTENSION postgis;"
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```

You will notice that the maps are not rendered. By default, Flask-Admin expects an integration with [Mapbox](https://www.mapbox.com/). To see them, you will have to register for a free account at [Mapbox](https://www.mapbox.com/) and set the `FLASK_ADMIN_MAPBOX_MAP_ID*` and `FLASK_ADMIN_MAPBOX_ACCESS_TOKEN` config variables accordingly.

However, some of the maps are overridden to use Open Street Maps

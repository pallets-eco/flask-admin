from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.rediscli import RedisCli
from redis import Redis
from testcontainers.redis import RedisContainer

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
admin = Admin(app, name="Example: RedisCLI")


@app.route("/")
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == "__main__":
    with RedisContainer() as redis_container:
        redis_client = redis_container.get_client()
        admin.add_view(
            RedisCli(
                Redis(
                    host=redis_container.get_container_host_ip(),
                    port=redis_container.get_exposed_port(redis_container.port),
                    password=redis_container.password,
                )
            )
        )

        app.run(debug=True)

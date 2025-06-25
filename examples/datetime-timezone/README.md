# Datetime Timezone Example

This example shows how to make Flask-Admin display all datetime fields in client's timezone. Timezone conversion is handled by the frontend in /static/js/timezone.js, but an automatic post request to /set_timezone is done so that flask session can store the client's timezone and save datetime inputs in the correct timezone.

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/datetime-timezone
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```

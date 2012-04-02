Adding new model backend
========================

If you want to implement new database backend to use with model views, follow steps from this guideline.

    1. Create new class and derive it from flask.ext.adminex.model.BaseModel::

        class DbModel(BaseModel):
            pass

    2. Implement following scaffolding methods::

        - `scaffold_list_columns`
            - Make sure you support `excluded_list_columns`
        - `scaffold_sortable_columns`
        - `scaffold_form`
            - Make sure you support `excluded_form_columns`
        - `init_search`

        If your database does not support free-form search,
        return `False` from the `init_search`.

        If your database does not support sorting, override
        `get_sortable_columns` and return empty dictionary.

    3. Implement data access methods::

        - `get_list`
        - `get_one`

    4. Implement model management methods
        - `create_model`
        - `update_model`
        - `delete_model`

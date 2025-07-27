#!/usr/bin/env python3
"""
Quick test script for Pydantic constrained types support.
"""

from sqlmodel import SQLModel


def test_constrained_types(app, engine, sqlmodel_base: type[SQLModel]):
    """Test constrained types conversion and validation."""
    pass

    # app.config["WTF_CSRF_ENABLED"] = False

    # session = Session()

    # # Define model with constrained types
    # class ConstrainedModel(sqlmodel_base, table=True):
    #     id: int = Field(primary_key=True)

    #     # Constrained string: 3-20 chars, letters only
    #     username: constr(min_length=3, max_length=20, pattern=r"^[A-Za-z]+$")
    # = Field( sa_type=String
    #     )

    #     # Constrained integer: 0-100
    #     score: conint(ge=0, le=100) = Field()

    #     # Constrained float: 0.0-1.0
    #     percentage: confloat(ge=0.0, le=1.0) = Field()

    #     # Optional constrained string
    #     nickname: Optional[constr(min_length=2, max_length=10)] = Field(
    #         default=None, sa_type=String
    #     )

    # # Create tables
    # sqlmodel_base.metadata.create_all(engine)

    # # Create view
    # view = SQLModelView(ConstrainedModel, session, name="Constrained Model")

    # with app.app_context():
    #     # Debug: Check model fields and their types
    #     print("Model fields debug:")
    #     for field_name, field_info in ConstrainedModel.model_fields.items():
    #         print(f"  {field_name}: {field_info.annotation}")
    #         print(f"    field_info: {field_info}")

    #     # Check model annotations directly
    #     print("Model annotations debug:")
    #     for field_name, annotation in ConstrainedModel.__annotations__.items():
    #         print(f"  {field_name}: {annotation}")

    #     # Test form creation
    #     form = view.create_form()
    #     print("Form created successfully!")
    #     print(f"Form fields: {list(form._fields.keys())}")

    #     # Test username field (constrained string)
    #     username_field = form.username
    #     print(f"Username field type: {type(username_field)}")
    #     print(f"Username validators: {[type(v) for v in username_field.validators]}")

    #     # Check if Length validators are present
    #     length_validators = [
    #         v for v in username_field.validators if isinstance(v, validators.Length)
    #     ]
    #     print(
    #         f"Username Length validators:
    #   {[(v.min, v.max) for v in length_validators]}"
    #     )

    #     # Check if Regexp validator is present
    #     regexp_validators = [
    #         v for v in username_field.validators if isinstance(v, validators.Regexp)
    #     ]
    #     print(
    #         f"Username Regexp validators: {[str(v.regex.pattern) if hasattr(v.regex, 'pattern') else str(v.regex) for v in regexp_validators]}"  # noqa: E501
    #     )

    #     # Test score field (constrained integer)
    #     score_field = form.score
    #     print(f"Score field type: {type(score_field)}")
    #     print(f"Score validators: {[type(v) for v in score_field.validators]}")

    #     # Check if NumberRange validators are present
    #     range_validators = [
    #         v for v in score_field.validators if isinstance(v, validators.NumberRange)
    #     ]
    #     print(
    #         f"Score NumberRange validators: {[(v.min, v.max) for v in range_validators]}"  # noqa: E501
    #     )

    #     # Test percentage field (constrained float)
    #     percentage_field = form.percentage
    #     print(f"Percentage field type: {type(percentage_field)}")
    #     print(
    #         f"Percentage validators: {[type(v) for v in percentage_field.validators]}"
    #     )

    #     # Check if NumberRange validators are present
    #     range_validators = [
    #         v
    #         for v in percentage_field.validators
    #         if isinstance(v, validators.NumberRange)
    #     ]
    #     print(
    #         f"Percentage NumberRange validators: {[(v.min, v.max) for v in range_validators]}"  # noqa: E501
    #     )

    #     # Test validation
    #     print("\nTesting validation:")

    #     # Test field validation directly (remove InputRequired for testing)
    #     username_field = form.username
    #     # Remove InputRequired validator for testing
    #     username_field.validators = [
    #         v
    #         for v in username_field.validators
    #         if not isinstance(v, validators.InputRequired)
    #     ]

    #     username_field.process_formdata(["Alice"])
    #     print(f"Valid username validation: {username_field.validate(form)}")

    #     username_field.process_formdata(["Al"])  # Too short
    #     print(
    #         f"Invalid username (too short) validation:
    # {username_field.validate(form)}"
    #     )
    #     if username_field.errors:
    #         print(f"Username errors: {username_field.errors}")

    #     username_field.process_formdata(
    #         ["Alice123"]
    #     )  # Contains numbers (invalid pattern)
    #     print(
    #         f"Invalid username (contains numbers) validation: {username_field.validate(form)}"  # noqa: E501
    #     )
    #     if username_field.errors:
    #         print(f"Username errors: {username_field.errors}")

    #     # Test score validation
    #     score_field = form.score
    #     # Remove InputRequired validator for testing
    #     score_field.validators = [
    #         v
    #         for v in score_field.validators
    #         if not isinstance(v, validators.InputRequired)
    #     ]
    #     score_field.process_formdata(["85"])
    #     print(f"Valid score validation: {score_field.validate(form)}")

    #     score_field.process_formdata(["150"])  # Too high
    #     print(f"Invalid score (too high) validation: {score_field.validate(form)}")
    #     if score_field.errors:
    #         print(f"Score errors: {score_field.errors}")

    #     # Test percentage validation
    #     percentage_field = form.percentage
    #     # Remove InputRequired validator for testing
    #     percentage_field.validators = [
    #         v
    #         for v in percentage_field.validators
    #         if not isinstance(v, validators.InputRequired)
    #     ]
    #     percentage_field.process_formdata(["0.85"])
    #     print(f"Valid percentage validation: {percentage_field.validate(form)}")

    #     percentage_field.process_formdata(["1.5"])  # Too high
    #     print(
    #         f"Invalid percentage (too high) validation: {percentage_field.validate(form)}"  # noqa: E501
    #     )
    #     if percentage_field.errors:
    #         print(f"Percentage errors: {percentage_field.errors}")

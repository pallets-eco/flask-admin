"""
Integration tests for Pydantic constrained types in SQLModel forms.

This file tests the complete integration of Pydantic constrained types including:
- constr (constrained string) with min_length, max_length, pattern
- conint (constrained integer) with ge, le, gt, lt
- confloat (constrained float) with ge, le, gt, lt
- Proper form generation, validation, and constraint handling
"""

from typing import Optional

from pydantic import confloat
from pydantic import conint
from pydantic import constr
from sqlalchemy import String
from sqlmodel import Field
from sqlmodel import SQLModel
from wtforms import fields
from wtforms import validators

from flask_admin.contrib.sqlmodel.view import SQLModelView


class TestConstrainedPydanticTypesIntegration:
    """Integration tests for constrained Pydantic field types."""

    def test_constrained_string_conversion(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test constr field conversion and validation."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class ConstrainedStringModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            # Constrained string: 3-20 chars, letters only
            username: constr(min_length=3, max_length=20, pattern=r"^[A-Za-z]+$") = (  # type: ignore
                Field(sa_type=String)
            )
            # Optional constrained string
            nickname: Optional[constr(min_length=2, max_length=10)] = Field(  # type: ignore
                default=None, sa_type=String
            )

        # Create the view with proper session
        view = SQLModelView(
            ConstrainedStringModel, session, name="Constrained String Model"
        )

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            # Test username field (constrained string)
            assert hasattr(form, "username")
            assert isinstance(form.username, fields.StringField)  # type: ignore

            # Check for Length validators
            length_validators = [
                v
                for v in form.username.validators # type: ignore
                if isinstance(v, validators.Length)
            ]
            assert len(length_validators) == 2  # min and max length
            min_lengths = [v.min for v in length_validators if v.min != -1]
            max_lengths = [v.max for v in length_validators if v.max != -1]
            assert 3 in min_lengths
            assert 20 in max_lengths

            # Check for Regexp validator
            regexp_validators = [
                v
                for v in form.username.validators # type: ignore
                if isinstance(v, validators.Regexp)  # type: ignore
            ]
            assert len(regexp_validators) == 1
            pattern = (
                regexp_validators[0].regex.pattern
                if hasattr(regexp_validators[0].regex, "pattern")
                else str(regexp_validators[0].regex)
            )
            assert pattern == "^[A-Za-z]+$"

            # Test nickname field (optional constrained string)
            assert hasattr(form, "nickname")
            assert isinstance(form.nickname, fields.StringField)  # type: ignore

    def test_constrained_integer_conversion(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test conint field conversion and validation."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class ConstrainedIntModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            # Constrained integer: 0-100
            score: conint(ge=0, le=100) = Field()  # type: ignore
            # Constrained integer: greater than 0, less than 1000
            points: conint(gt=0, lt=1000) = Field()  # type: ignore
            # Optional constrained integer
            bonus: Optional[conint(ge=0, le=50)] = Field(default=None)  # type: ignore

        # Create the view with proper session
        view = SQLModelView(ConstrainedIntModel, session, name="Constrained Int Model")

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            # Test score field (ge/le constraints)
            assert hasattr(form, "score")
            assert isinstance(form.score, fields.IntegerField)  # type: ignore

            range_validators = [
                v
                for v in form.score.validators  # type: ignore
                if isinstance(v, validators.NumberRange)
            ]
            assert len(range_validators) == 1
            assert range_validators[0].min == 0
            assert range_validators[0].max == 100

            # Test points field (gt/lt constraints - should
            # be converted to ge/le with adjustment)
            assert hasattr(form, "points")
            assert isinstance(form.points, fields.IntegerField)  # type: ignore

            range_validators = [
                v
                for v in form.points.validators  # type: ignore
                if isinstance(v, validators.NumberRange)
            ]
            assert len(range_validators) == 1
            # gt=0 becomes ge=1, lt=1000 becomes le=999
            assert range_validators[0].min == 1  # gt 0 -> ge 1
            assert range_validators[0].max == 999  # lt 1000 -> le 999

            # Test bonus field (optional)
            assert hasattr(form, "bonus")
            assert isinstance(form.bonus, fields.IntegerField)  # type: ignore

    def test_constrained_float_conversion(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test confloat field conversion and validation."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class ConstrainedFloatModel(sqlmodel_base, table=True):
            id: int = Field(primary_key=True)
            name: str
            # Constrained float: 0.0-1.0 (percentage)
            percentage: confloat(ge=0.0, le=1.0) = Field()  # type: ignore
            # Constrained float: greater than 0.0
            rating: confloat(gt=0.0, lt=10.0) = Field()  # type: ignore
            # Optional constrained float
            weight: Optional[confloat(ge=0.0)] = Field(default=None)  # type: ignore

        # Create the view with proper session
        view = SQLModelView(
            ConstrainedFloatModel, session, name="Constrained Float Model"
        )

        with app.app_context():
            # Test form generation
            form = view.create_form()
            assert form is not None

            # Test percentage field (ge/le constraints)
            assert hasattr(form, "percentage")
            assert isinstance(form.percentage, fields.DecimalField)  # type: ignore

            range_validators = [
                v
                for v in form.percentage.validators  # type: ignore
                if isinstance(v, validators.NumberRange)
            ]
            assert len(range_validators) == 1
            assert range_validators[0].min == 0.0
            assert range_validators[0].max == 1.0

            # Test rating field (gt/lt constraints)
            assert hasattr(form, "rating")
            assert isinstance(form.rating, fields.DecimalField)  # type: ignore

            range_validators = [
                v
                for v in form.rating.validators  # type: ignore
                if isinstance(v, validators.NumberRange)
            ]
            assert len(range_validators) == 1
            # gt=0.0 becomes ge=0.001, lt=10.0 becomes le=9.999
            assert range_validators[0].min == 0.001  # gt 0.0 -> ge 0.001
            assert range_validators[0].max == 9.999  # lt 10.0 -> le 9.999

            # Test weight field (optional, only lower bound)
            assert hasattr(form, "weight")
            assert isinstance(form.weight, fields.DecimalField)  # type: ignore

    def test_constrained_types_validation_behavior(
        self, app, engine, babel, sqlmodel_base: type[SQLModel]
    ):
        """Test that constrained field validators work correctly."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        class ValidationTestModel(sqlmodel_base, table=True):
            __tablename__ = "validation_test"  # type: ignore

            id: int = Field(primary_key=True)
            username: constr(min_length=3, max_length=10) = Field(sa_type=String)  # type: ignore
            score: conint(ge=0, le=100) = Field()  # type: ignore
            percentage: confloat(ge=0.0, le=1.0) = Field()  # type: ignore

        view = SQLModelView(ValidationTestModel, session, name="Validation Test")

        with app.app_context():
            form = view.create_form()

            # Test username validation (remove InputRequired for testing)
            username_field = form.username  # type: ignore
            username_field.validators = [
                v
                for v in username_field.validators
                if not isinstance(v, validators.InputRequired)
            ]

            # Valid username
            username_field.process_formdata(["Alice"])
            assert username_field.validate(form)

            # Invalid username (too short)
            username_field.process_formdata(["Al"])
            assert not username_field.validate(form)
            assert any(
                "at least 3 characters" in str(error) for error in username_field.errors
            )

            # Invalid username (too long)
            username_field.process_formdata(["ThisIsTooLong"])
            assert not username_field.validate(form)
            # Check that there's at least one error (error message format may vary)
            assert len(username_field.errors) > 0
            print(f"Username validation errors: {username_field.errors}")  # Debug print

            # Test score validation
            score_field = form.score # type: ignore
            score_field.validators = [
                v
                for v in score_field.validators
                if not isinstance(v, validators.InputRequired)
            ]

            # Valid score
            score_field.process_formdata(["50"])
            assert score_field.validate(form)

            # Invalid score (too high)
            score_field.process_formdata(["150"])
            assert not score_field.validate(form)
            assert any(
                "between 0 and 100" in str(error) for error in score_field.errors
            )

            # Test percentage validation
            percentage_field = form.percentage  # type: ignore
            percentage_field.validators = [
                v
                for v in percentage_field.validators
                if not isinstance(v, validators.InputRequired)
            ]

            # Valid percentage
            percentage_field.process_formdata(["0.75"])
            assert percentage_field.validate(form)

            # Invalid percentage (too high)
            percentage_field.process_formdata(["1.5"])
            assert not percentage_field.validate(form)
            assert any(
                "between 0.0 and 1.0" in str(error) for error in percentage_field.errors
            )

    def test_constrained_types_compatibility(self, sqlmodel_base: type[SQLModel]):
        """Test constrained types detection and fallback behavior."""

        # Test constraint detection functions
        from flask_admin.contrib.sqlmodel.tools import get_pydantic_field_constraints
        from flask_admin.contrib.sqlmodel.tools import is_pydantic_constrained_type
        from flask_admin.contrib.sqlmodel.tools import (
            PYDANTIC_CONSTRAINED_TYPES_AVAILABLE,
        )

        # These should be boolean values, not None
        assert isinstance(PYDANTIC_CONSTRAINED_TYPES_AVAILABLE, bool)

        if PYDANTIC_CONSTRAINED_TYPES_AVAILABLE:
            # Test constrained type detection
            constrained_str = constr(min_length=3, max_length=10)
            constrained_int = conint(ge=0, le=100)
            constrained_float = confloat(ge=0.0, le=1.0)

            assert is_pydantic_constrained_type(constrained_str)
            assert is_pydantic_constrained_type(constrained_int)
            assert is_pydantic_constrained_type(constrained_float)
            assert not is_pydantic_constrained_type(str)
            assert not is_pydantic_constrained_type(int)

            # Test constraint extraction
            str_constraints = get_pydantic_field_constraints(None, constrained_str)
            assert str_constraints["min_length"] == 3
            assert str_constraints["max_length"] == 10

            int_constraints = get_pydantic_field_constraints(None, constrained_int)
            assert int_constraints["min_value"] == 0
            assert int_constraints["max_value"] == 100

            float_constraints = get_pydantic_field_constraints(None, constrained_float)
            assert float_constraints["min_value"] == 0.0
            assert float_constraints["max_value"] == 1.0

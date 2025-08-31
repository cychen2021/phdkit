"""Tests for the configlib module, including postload functionality."""

import tempfile
import os
import pytest
from phdkit.configlib.configurable import configurable, setting, Config, config


class TestPostloadFunctionality:
    """Test the postload functionality of the configurable decorator."""

    def test_postload_called_after_config_load(self):
        """Test that postload function is called after configuration loading."""
        # Track if postload was called
        postload_called = False
        postload_instance = None

        def my_postload(instance):
            nonlocal postload_called, postload_instance
            postload_called = True
            postload_instance = instance

        # Define a configurable class with postload
        @configurable(
            load_config=lambda config_file: {'name': 'test', 'value': 42} if config_file else {},
            postload=my_postload
        )
        class TestClass:
            @setting('name')
            def name(self):
                pass

            @setting('value')
            def value(self):
                pass

        # Create instance and load config
        instance = TestClass()
        config[instance].load("dummy")

        # Verify postload was called
        assert postload_called, "Postload function should have been called"
        assert postload_instance is instance, "Postload should receive the correct instance"

        # Verify config was loaded
        assert instance.name == "test"
        assert instance.value == 42

    def test_postload_registered_as_member_function(self):
        """Test that postload function is registered as a member function of the class."""
        def my_postload(instance):
            pass

        @configurable(
            load_config=lambda config_file: {},
            postload=my_postload
        )
        class TestClass:
            pass

        # Check that the class has the postload method
        assert hasattr(TestClass, 'postload'), "Class should have postload as a member function"
        assert getattr(TestClass, 'postload') is my_postload, "Postload should be the registered function"

        # Create instance and check it has the method
        instance = TestClass()
        assert hasattr(instance, 'postload'), "Instance should have postload method"
        assert callable(getattr(instance, 'postload')), "Instance postload should be callable"

    def test_postload_without_function(self):
        """Test that configurable works without postload function."""
        @configurable(
            load_config=lambda config_file: {'name': 'test'} if config_file else {},
        )
        class TestClass:
            name = setting('name')

        # Should not have postload method
        assert not hasattr(TestClass, 'postload'), "Class should not have postload when not provided"

        instance = TestClass()
        assert not hasattr(instance, 'postload'), "Instance should not have postload when not provided"

    def test_postload_with_inheritance(self):
        """Test postload functionality with class inheritance."""
        parent_postload_called = False
        child_postload_called = False

        def parent_postload(instance):
            nonlocal parent_postload_called
            parent_postload_called = True

        def child_postload(instance):
            nonlocal child_postload_called
            child_postload_called = True

        @configurable(
            load_config=lambda config_file: {'name': 'parent', 'value': 100, 'child_value': 200} if config_file else {},
            postload=parent_postload
        )
        class ParentClass:
            @setting('name')
            def name(self):
                pass

        @configurable(
            load_config=lambda config_file: {'name': 'parent', 'value': 100, 'child_value': 200} if config_file else {},
            postload=child_postload
        )
        class ChildClass(ParentClass):
            @setting('value')
            def value(self):
                pass

            @setting('child_value')
            def child_value(self):
                pass

        # Load config for child class
        child_instance = ChildClass()
        config[child_instance].load("dummy")

        # Child postload should be called (most specific)
        assert child_postload_called, "Child postload should be called"
        assert not parent_postload_called, "Parent postload should not be called for child instance"

        # Verify config loading
        assert child_instance.name == "parent"
        assert child_instance.value == 100
        assert child_instance.child_value == 200

    def test_postload_exception_handling(self):
        """Test that exceptions in postload are not caught by the config loader."""
        def failing_postload(instance):
            raise ValueError("Postload failed")

        @configurable(
            load_config=lambda config_file: {'name': 'test'} if config_file else {},
            postload=failing_postload
        )
        class TestClass:
            @setting('name')
            def name(self):
                pass

        instance = TestClass()

        # Should raise the exception from postload
        with pytest.raises(ValueError, match="Postload failed"):
            config[instance].load("dummy")

    def test_postload_with_config_update(self):
        """Test updating postload function via config update."""
        def original_postload(instance):
            instance.postload_called = "original"

        def updated_postload(instance):
            instance.postload_called = "updated"

        @configurable(
            load_config=lambda config_file: {'name': 'test'} if config_file else {},
            postload=original_postload
        )
        class TestClass:
            @setting('name')
            def name(self):
                pass

        # Update with new postload
        Config.update(TestClass, postload=updated_postload)

        instance = TestClass()
        config[instance].load("dummy")

        # Should call the updated postload
        assert hasattr(instance, 'postload_called'), "Postload should have been called"
        assert getattr(instance, 'postload_called') == "updated", "Updated postload should be called"

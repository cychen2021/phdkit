"""Tests for the configlib module, including postload functionality."""

import pytest
from phdkit.configlib.configurable import configurable, setting, Config, config
from phdkit.configlib.tomlreader import TomlReader


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
            load_config=lambda config_file: {"name": "test", "value": 42}
            if config_file
            else {},
            postload=my_postload,
        )
        class TestClass:
            @setting("name")
            def name(self):
                pass

            @setting("value")
            def value(self):
                pass

        # Create instance and load config
        instance = TestClass()
        config[instance].load("dummy")

        # Verify postload was called
        assert postload_called, "Postload function should have been called"
        assert postload_instance is instance, (
            "Postload should receive the correct instance"
        )

        # Verify config was loaded
        assert instance.name == "test"
        assert instance.value == 42

    def test_postload_registered_as_member_function(self):
        """Test that postload function is registered as a member function of the class."""

        def my_postload(instance):
            pass

        @configurable(load_config=lambda config_file: {}, postload=my_postload)
        class TestClass:
            pass

        # Check that the class has the postload method
        assert hasattr(TestClass, "postload"), (
            "Class should have postload as a member function"
        )
        assert getattr(TestClass, "postload") is my_postload, (
            "Postload should be the registered function"
        )

        # Create instance and check it has the method
        instance = TestClass()
        assert hasattr(instance, "postload"), "Instance should have postload method"
        assert callable(getattr(instance, "postload")), (
            "Instance postload should be callable"
        )

    def test_postload_without_function(self):
        """Test that configurable works without postload function."""

        @configurable(
            load_config=lambda config_file: {"name": "test"} if config_file else {},
        )
        class TestClass:
            name = setting("name")

        # Should not have postload method
        assert not hasattr(TestClass, "postload"), (
            "Class should not have postload when not provided"
        )

        instance = TestClass()
        assert not hasattr(instance, "postload"), (
            "Instance should not have postload when not provided"
        )

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
            load_config=lambda config_file: {
                "name": "parent",
                "value": 100,
                "child_value": 200,
            }
            if config_file
            else {},
            postload=parent_postload,
        )
        class ParentClass:
            @setting("name")
            def name(self):
                pass

        @configurable(
            load_config=lambda config_file: {
                "name": "parent",
                "value": 100,
                "child_value": 200,
            }
            if config_file
            else {},
            postload=child_postload,
        )
        class ChildClass(ParentClass):
            @setting("value")
            def value(self):
                pass

            @setting("child_value")
            def child_value(self):
                pass

        # Load config for child class
        child_instance = ChildClass()
        config[child_instance].load("dummy")

        # Child postload should be called (most specific)
        assert child_postload_called, "Child postload should be called"
        assert not parent_postload_called, (
            "Parent postload should not be called for child instance"
        )

        # Verify config loading
        assert child_instance.name == "parent"
        assert child_instance.value == 100
        assert child_instance.child_value == 200

    def test_postload_exception_handling(self):
        """Test that exceptions in postload are not caught by the config loader."""

        def failing_postload(instance):
            raise ValueError("Postload failed")

        @configurable(
            load_config=lambda config_file: {"name": "test"} if config_file else {},
            postload=failing_postload,
        )
        class TestClass:
            @setting("name")
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
            load_config=lambda config_file: {"name": "test"} if config_file else {},
            postload=original_postload,
        )
        class TestClass:
            @setting("name")
            def name(self):
                pass

        # Update with new postload
        Config.update(TestClass, postload=updated_postload)

        instance = TestClass()
        config[instance].load("dummy")

        # Should call the updated postload
        assert hasattr(instance, "postload_called"), "Postload should have been called"
        assert getattr(instance, "postload_called") == "updated", (
            "Updated postload should be called"
        )


class TestArrayHandling:
    """Test that configlib handles arrays in TOML correctly."""

    def test_array_setting_with_list_values(self):
        """Test loading an array setting with list values from TOML."""
        import tempfile
        import os

        # Create a temporary TOML file with array data
        toml_content = """
        [config]
        items = ["apple", "banana", "cherry"]
        numbers = [1, 2, 3, 4, 5]
        mixed = ["string", 42, true, 3.14]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("config.items")
                def items(self):
                    pass

                @setting("config.numbers")
                def numbers(self):
                    pass

                @setting("config.mixed")
                def mixed(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify arrays are loaded correctly
            assert instance.items == ["apple", "banana", "cherry"]
            assert instance.numbers == [1, 2, 3, 4, 5]
            assert instance.mixed == ["string", 42, True, 3.14]

        finally:
            os.unlink(temp_file)

    def test_nested_array_setting(self):
        """Test loading nested arrays from TOML."""
        import tempfile
        import os

        # Create a temporary TOML file with nested array data
        toml_content = """
        [config]
        matrix = [[1, 2], [3, 4], [5, 6]]
        nested = [["a", "b"], ["c", "d"]]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("config.matrix")
                def matrix(self):
                    pass

                @setting("config.nested")
                def nested(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify nested arrays are loaded correctly
            assert instance.matrix == [[1, 2], [3, 4], [5, 6]]
            assert instance.nested == [["a", "b"], ["c", "d"]]

        finally:
            os.unlink(temp_file)

    def test_empty_array_setting(self):
        """Test loading an empty array from TOML."""
        import tempfile
        import os

        # Create a temporary TOML file with empty array
        toml_content = """
        [config]
        empty_list = []
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("config.empty_list")
                def empty_list(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify empty array is loaded correctly
            assert instance.empty_list == []

        finally:
            os.unlink(temp_file)

    def test_array_with_default_values(self):
        """Test array settings with default values when key is missing."""
        import tempfile
        import os

        # Create a temporary TOML file without the array key
        toml_content = """
        [config]
        other_setting = "value"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("config.missing_array", default=[1, 2, 3])
                def missing_array(self):
                    pass

                @setting("config.other_setting")
                def other_setting(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify default array is used when key is missing
            assert instance.missing_array == [1, 2, 3]
            assert instance.other_setting == "value"

        finally:
            os.unlink(temp_file)

    def test_array_setting_type_preservation(self):
        """Test that array element types are preserved from TOML."""
        import tempfile
        import os

        # Create a temporary TOML file with different types in array
        toml_content = """
        [config]
        strings = ["hello", "world"]
        integers = [10, 20, 30]
        floats = [1.1, 2.2, 3.3]
        booleans = [true, false, true]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("config.strings")
                def strings(self):
                    pass

                @setting("config.integers")
                def integers(self):
                    pass

                @setting("config.floats")
                def floats(self):
                    pass

                @setting("config.booleans")
                def booleans(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify types are preserved
            assert instance.strings == ["hello", "world"]
            assert all(isinstance(s, str) for s in instance.strings)  # type: ignore

            assert instance.integers == [10, 20, 30]
            assert all(isinstance(i, int) for i in instance.integers)  # type: ignore

            assert instance.floats == [1.1, 2.2, 3.3]
            assert all(isinstance(f, float) for f in instance.floats)  # type: ignore

            assert instance.booleans == [True, False, True]
            assert all(isinstance(b, bool) for b in instance.booleans)  # type: ignore

        finally:
            os.unlink(temp_file)

    def test_array_of_tables_setting(self):
        """Test loading an array of tables from TOML using [[array_name]] syntax."""
        import tempfile
        import os

        # Create a temporary TOML file with array of tables
        toml_content = """
        [[items]]
        name = "apple"
        value = 1

        [[items]]
        name = "banana"
        value = 2

        [[items]]
        name = "cherry"
        value = 3
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("items")
                def items(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify array of tables is loaded correctly
            expected = [
                {"name": "apple", "value": 1},
                {"name": "banana", "value": 2},
                {"name": "cherry", "value": 3},
            ]
            assert instance.items == expected

        finally:
            os.unlink(temp_file)

    def test_nested_array_of_tables_setting(self):
        """Test loading nested arrays of tables from TOML."""
        import tempfile
        import os

        # Create a temporary TOML file with nested array of tables
        toml_content = """
        [[servers]]
        name = "web"
        
        [[servers.hosts]]
        ip = "192.168.1.1"
        port = 80
        
        [[servers.hosts]]
        ip = "192.168.1.2"
        port = 443

        [[servers]]
        name = "db"
        
        [[servers.hosts]]
        ip = "192.168.2.1"
        port = 5432
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("servers")
                def servers(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify nested array of tables is loaded correctly
            expected = [
                {
                    "name": "web",
                    "hosts": [
                        {"ip": "192.168.1.1", "port": 80},
                        {"ip": "192.168.1.2", "port": 443},
                    ],
                },
                {"name": "db", "hosts": [{"ip": "192.168.2.1", "port": 5432}]},
            ]
            assert instance.servers == expected

        finally:
            os.unlink(temp_file)

    def test_empty_array_of_tables_setting(self):
        """Test loading an empty array of tables from TOML."""
        import tempfile
        import os

        # Create a temporary TOML file with no array of tables (empty)
        toml_content = """
        [config]
        other_setting = "value"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_file = f.name

        try:

            @configurable(load_config=TomlReader(temp_file))
            class TestClass:
                @setting("items", default=[])
                def items(self):
                    pass

                @setting("config.other_setting")
                def other_setting(self):
                    pass

            instance = TestClass()
            config[instance].load()

            # Verify empty array of tables defaults to empty list
            assert instance.items == []
            assert instance.other_setting == "value"

        finally:
            os.unlink(temp_file)

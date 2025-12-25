"""Tests for HTTP operations (FETCH, POST)."""

import pytest
import responses

from anka.grammar.parser import Parser
from anka.runtime.interpreter import Interpreter
from anka.runtime.interpreter import RuntimeError as AnkaRuntimeError


@pytest.fixture
def parser() -> Parser:
    """Create a parser instance."""
    return Parser()


@pytest.fixture
def interpreter() -> Interpreter:
    """Create an interpreter instance."""
    return Interpreter()


class TestFetchOperation:
    """Tests for the FETCH operation."""

    @responses.activate
    def test_fetch_get_json_array(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test fetching a JSON array."""
        responses.add(
            responses.GET,
            "https://api.example.com/users",
            json=[
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            status=200,
        )

        source = '''
        PIPELINE fetch_test:
            INPUT dummy: TABLE[x: INT]

            STEP get_users:
                FETCH "https://api.example.com/users"
                METHOD GET
                INTO users

            OUTPUT users
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    @responses.activate
    def test_fetch_get_json_object(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test fetching a JSON object (non-array)."""
        responses.add(
            responses.GET,
            "https://api.example.com/user/1",
            json={"id": 1, "name": "Alice"},
            status=200,
        )

        source = '''
        PIPELINE fetch_object:
            INPUT dummy: TABLE[x: INT]

            STEP get_user:
                FETCH "https://api.example.com/user/1"
                METHOD GET
                INTO user

            OUTPUT user
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        # Non-array responses are wrapped in a response object
        assert result is not None
        assert len(result) == 1
        assert result[0]["status"] == 200
        assert result[0]["body"]["name"] == "Alice"

    @responses.activate
    def test_fetch_with_headers(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test fetching with custom headers."""
        def request_callback(request):  # type: ignore[no-untyped-def]
            assert request.headers.get("Authorization") == "Bearer token123"
            return (200, {}, '[{"id": 1}]')

        responses.add_callback(
            responses.GET,
            "https://api.example.com/secure",
            callback=request_callback,
            content_type="application/json",
        )

        source = '''
        PIPELINE fetch_secure:
            INPUT dummy: TABLE[x: INT]

            STEP get_data:
                FETCH "https://api.example.com/secure"
                METHOD GET
                HEADERS {"Authorization": "Bearer token123"}
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 1

    @responses.activate
    def test_fetch_with_env_var_in_url(
        self, parser: Parser, interpreter: Interpreter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fetching with environment variable in URL."""
        monkeypatch.setenv("API_HOST", "api.example.com")

        responses.add(
            responses.GET,
            "https://api.example.com/data",
            json=[{"x": 1}],
            status=200,
        )

        source = '''
        PIPELINE fetch_env:
            INPUT dummy: TABLE[x: INT]

            STEP get_data:
                FETCH "https://${API_HOST}/data"
                METHOD GET
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None

    @responses.activate
    def test_fetch_with_env_var_in_headers(
        self, parser: Parser, interpreter: Interpreter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fetching with environment variable in headers."""
        monkeypatch.setenv("API_KEY", "secret123")

        def request_callback(request):  # type: ignore[no-untyped-def]
            assert request.headers.get("X-API-Key") == "secret123"
            return (200, {}, '[{"id": 1}]')

        responses.add_callback(
            responses.GET,
            "https://api.example.com/data",
            callback=request_callback,
            content_type="application/json",
        )

        source = '''
        PIPELINE fetch_env_header:
            INPUT dummy: TABLE[x: INT]

            STEP get_data:
                FETCH "https://api.example.com/data"
                METHOD GET
                HEADERS {"X-API-Key": "${API_KEY}"}
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None

    @responses.activate
    def test_fetch_and_filter(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test fetching and filtering response data."""
        responses.add(
            responses.GET,
            "https://api.example.com/orders",
            json=[
                {"id": 1, "amount": 500},
                {"id": 2, "amount": 1500},
                {"id": 3, "amount": 2000},
            ],
            status=200,
        )

        source = '''
        PIPELINE fetch_filter:
            INPUT dummy: TABLE[x: INT]

            STEP get_orders:
                FETCH "https://api.example.com/orders"
                METHOD GET
                INTO orders

            STEP filter_large:
                FILTER orders
                WHERE amount > 1000
                INTO large_orders

            OUTPUT large_orders
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 2
        assert all(row["amount"] > 1000 for row in result)

    @responses.activate
    def test_fetch_network_error(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test error handling for network failures."""
        from requests.exceptions import ConnectionError

        responses.add(
            responses.GET,
            "https://api.example.com/fail",
            body=ConnectionError("Connection refused"),
        )

        source = '''
        PIPELINE fetch_fail:
            INPUT dummy: TABLE[x: INT]

            STEP get_data:
                FETCH "https://api.example.com/fail"
                METHOD GET
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        with pytest.raises(AnkaRuntimeError, match="HTTP request failed"):
            interpreter.execute(ast, {"dummy": []})


class TestPostOperation:
    """Tests for the POST operation."""

    @responses.activate
    def test_post_with_object_literal(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test POST with inline object literal body."""
        def request_callback(request):  # type: ignore[no-untyped-def]
            import json
            body = json.loads(request.body)
            assert body["name"] == "Alice"
            assert body["email"] == "alice@example.com"
            return (201, {}, '{"id": 1, "name": "Alice"}')

        responses.add_callback(
            responses.POST,
            "https://api.example.com/users",
            callback=request_callback,
            content_type="application/json",
        )

        source = '''
        PIPELINE post_test:
            INPUT dummy: TABLE[x: INT]

            STEP create_user:
                POST "https://api.example.com/users"
                BODY {"name": "Alice", "email": "alice@example.com"}
                INTO response

            OUTPUT response
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 1
        assert result[0]["status"] == 201

    @responses.activate
    def test_post_with_variable_body(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test POST with variable reference as body."""
        def request_callback(request):  # type: ignore[no-untyped-def]
            import json
            body = json.loads(request.body)
            assert len(body) == 2
            return (201, {}, '{"created": 2}')

        responses.add_callback(
            responses.POST,
            "https://api.example.com/batch",
            callback=request_callback,
            content_type="application/json",
        )

        source = '''
        PIPELINE post_var:
            INPUT data: TABLE[id: INT, name: STRING]

            STEP send_data:
                POST "https://api.example.com/batch"
                BODY data
                INTO response

            OUTPUT response
        '''
        input_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": input_data})

        assert result is not None
        assert result[0]["status"] == 201

    @responses.activate
    def test_post_with_headers(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test POST with custom headers."""
        def request_callback(request):  # type: ignore[no-untyped-def]
            assert request.headers.get("X-Custom-Header") == "custom-value"
            return (200, {}, '{"ok": true}')

        responses.add_callback(
            responses.POST,
            "https://api.example.com/data",
            callback=request_callback,
            content_type="application/json",
        )

        source = '''
        PIPELINE post_headers:
            INPUT dummy: TABLE[x: INT]

            STEP send:
                POST "https://api.example.com/data"
                BODY {"key": "value"}
                HEADERS {"X-Custom-Header": "custom-value"}
                INTO response

            OUTPUT response
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None

    @responses.activate
    def test_post_body_var_not_found(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test error when body variable doesn't exist."""
        responses.add(
            responses.POST,
            "https://api.example.com/data",
            json={"ok": True},
            status=200,
        )

        source = '''
        PIPELINE post_missing_var:
            INPUT dummy: TABLE[x: INT]

            STEP send:
                POST "https://api.example.com/data"
                BODY nonexistent
                INTO response

            OUTPUT response
        '''
        ast = parser.parse(source)
        with pytest.raises(AnkaRuntimeError, match="not found in environment"):
            interpreter.execute(ast, {"dummy": []})


class TestHTTPMethods:
    """Tests for different HTTP methods."""

    @responses.activate
    def test_fetch_delete(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test DELETE method."""
        responses.add(
            responses.DELETE,
            "https://api.example.com/users/1",
            json={"deleted": True},
            status=200,
        )

        source = '''
        PIPELINE delete_test:
            INPUT dummy: TABLE[x: INT]

            STEP delete_user:
                FETCH "https://api.example.com/users/1"
                METHOD DELETE
                INTO response

            OUTPUT response
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None

    @responses.activate
    def test_fetch_put(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test PUT method."""
        responses.add(
            responses.PUT,
            "https://api.example.com/users/1",
            json={"id": 1, "updated": True},
            status=200,
        )

        source = '''
        PIPELINE put_test:
            INPUT dummy: TABLE[x: INT]

            STEP update_user:
                FETCH "https://api.example.com/users/1"
                METHOD PUT
                INTO response

            OUTPUT response
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None

from auraframes.api.base_api import BaseApi
from auraframes.exceptions import AuthenticationError, APIError, ValidationError
from auraframes.models.user import User
from auraframes.utils import settings
from auraframes.utils.validation import validate_email, validate_password, validate_non_empty


class AccountApi(BaseApi):

    async def login(self, email: str, password: str) -> User:
        """
        Authenticates with the API.

        :param email: Registered email
        :param password: Registered password (plaintext)
        :return: Hydrated user object
        :raises ValidationError: If email or password format is invalid
        :raises AuthenticationError: If login fails
        """
        validate_email(email)
        validate_password(password)

        login_payload = {
            'user': {
                'email': email,
                'password': password
            },
            'locale': settings.LOCALE,
            'app_identifier': settings.AURA_APP_IDENTIFIER,
            'identifier_for_vendor': settings.DEVICE_IDENTIFIER,
            'client_device_id': settings.DEVICE_IDENTIFIER
        }

        json_response = await self._client.post('/login.json', login_payload)
        if json_response.get('error') or not json_response.get('result'):
            error_msg = json_response.get('error', 'Login failed')
            raise AuthenticationError(f"Login failed: {error_msg}")

        result = json_response.get('result', {})
        return User(**result.get('current_user', {}))

    async def register(self, email: str, password: str, name: str) -> User:
        """
        Registers an account.

        :param email: Email to register with
        :param password: Password (plaintext) to register with
        :param name: Display name
        :return: Hydrated user object for the registered user.
        :raises ValidationError: If email, password, or name format is invalid
        :raises APIError: If registration fails
        """
        validate_email(email)
        validate_password(password)
        validate_non_empty(name, "Name")

        register_payload = {
            'email': email,
            'name': name,
            'password': password,
            'identifier_for_vendor': settings.DEVICE_IDENTIFIER,
            'smart_suggestions_off': True,
            'auto_upload_off': True,
            'locale': settings.LOCALE,
            'client_device_id': settings.DEVICE_IDENTIFIER
        }

        json_response = await self._client.post('/account/register.json', data=register_payload)

        if json_response.get('error') or not json_response.get('result'):
            error_msg = json_response.get('error', 'Registration failed')
            raise APIError(f"Registration failed: {error_msg}")

        result = json_response.get('result', {})
        return User(**result.get('current_user', {}))

    async def delete(self) -> bool:
        """
        Deletes the currently logged in user.
        :return: Boolean describing if the user was successfully deleted.
        """
        json_response = await self._client.delete('/account/delete')

        result = json_response.get('result')
        return result is not None and result.get('success') and not json_response.get('error')

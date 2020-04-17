from ._base_auth import AuthProviderBase, TokenCredential
from ..constants import AUTH_MIDDLEWARE_OPTIONS, BASE_URL
from ._middleware import BaseMiddleware


class AuthorizationHandler(BaseMiddleware):
    def __init__(self, auth_provider: AuthProviderBase):
        super().__init__()
        self.auth_provider = auth_provider
        self.retry_count = 0

    def send(self, request, **kwargs):
        options = self._get_middleware_options(request)
        if options:
            self.auth_provider.scopes = options.scopes

        token = self.auth_provider.get_access_token()
        request.headers.update({'Authorization': 'Bearer {}'.format(token)})
        response = super().send(request, **kwargs)

        if response.status_code == 401 and self.retry_count < 2:
            self.retry_count += 1
            return self.send(request, **kwargs)

        return response

    def _get_middleware_options(self, request):
        return request.middleware_control.get(AUTH_MIDDLEWARE_OPTIONS)


class TokenCredentialAuthProvider(AuthProviderBase):
    def __init__(self, credential: TokenCredential, scopes: [str] = BASE_URL + '.default'):
        self.credential = credential
        self.scopes = scopes

    @property
    def scopes(self):
        return self._scopes

    @scopes.setter
    def scopes(self, list_of_scopes):
        if type(list_of_scopes) == list:
            graph_scopes = BASE_URL + '?scopes='

            for scope in list_of_scopes:
                graph_scopes += scope + '%20'

            self._scopes = graph_scopes
        elif type(list_of_scopes) == str:
            self._scopes = list_of_scopes

    def get_access_token(self):
        return self.credential.get_token(self.scopes)[0]
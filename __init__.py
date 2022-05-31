# pylint: disable=missing-module-docstring,line-too-long
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class JiraCloud:
    """Python library to make interacting with the Jira Cloud API easy.
    """
    def __init__(self, atlassian_cloud_domain: str, username: str, api_token: str, api_version: int = 3):
        """Create the JiraCloud object to begin making API calls.

        Args:
            atlassian_cloud_domain (str): The first part of your Atlassian cloud domain. Ex: https://your-domain.atlassian.net/ -> your-domain
            username (str): Username of API user.
            api_token (str): API token for API user.
            api_version (int, optional): Ability to switch to a different API version if necessary. Defaults to 3.
        """
        self.base_url = f'https://{atlassian_cloud_domain}.atlassian.net/rest/api/{api_version}/'
        self.atlassian_cloud_domain = atlassian_cloud_domain
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        self.timeout = 10
        adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1))
        self.session.mount('https://', adapter)

        # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-server-info/#api-rest-api-3-serverinfo-get
        self.__get('serverInfo')

    def __get(self, resource_path: str, params: dict = {}, raise_for_status: bool = True, full_url: bool = False) -> requests.models.Response:  # pylint: disable=dangerous-default-value
        """Make a GET request to Atlassian Cloud. Primarily to be used by other class functions.

        Args:
            resource_path (str): The resource path as shown in the API documentation. Ex: https://your-domain.atlassian.net/rest/api/3/issue/DEMO-1 -> issue/DEMO-1
            params (dict, optional): Query parameter to append to the resource path. Defaults to {}.
            raise_for_status (bool, optional): Whether or not to raise error if HTTP response is not okay. Defaults to True.
            full_url (bool, optional): If True, resource_path will be treated as a complete URL and will not be appended to the base URL. Defaults to False.

        Returns:
            requests.models.Response: Full requests response object.
        """
        if not full_url:
            req = self.session.get(self.base_url + resource_path, params=params, timeout=self.timeout)
        else:
            req = self.session.get(resource_path, params=params, timeout=self.timeout)
        if raise_for_status:
            req.raise_for_status()
        return req

    def __post(self, resource_path: str, params: dict = {}, body: dict = {}, raise_for_status: bool = True, full_url: bool = False) -> requests.models.Response:  # pylint: disable=dangerous-default-value
        """Make a POST request to Atlassian Cloud. Primarily to be used by other class functions.

        Args:
            resource_path (str): The resource path as shown in the API documentation. Ex: https://your-domain.atlassian.net/rest/api/3/issue/DEMO-1 -> issue/DEMO-1
            params (dict, optional): Query parameter to append to the resource path. Defaults to {}. Defaults to {}.
            body (dict, optional): Body of the request. Must be JSON. Defaults to {}.
            raise_for_status (bool, optional): Whether or not to raise error if HTTP response is not okay. Defaults to True.
            full_url (bool, optional): If True, resource_path will be treated as a complete URL and will not be appended to the base URL. Defaults to False.

        Returns:
            requests.models.Response: Full requests response object.
        """
        if not full_url:
            req = self.session.post(self.base_url + resource_path, params=params, json=body, headers={'Content-Type': 'application/json'}, timeout=self.timeout)
        else:
            req = self.session.post(resource_path, params=params, json=body, headers={'Content-Type': 'application/json'}, timeout=self.timeout)
        if raise_for_status:
            req.raise_for_status()
        return req

    def search_issues(self, jql: str) -> list:
        """Search for Jira issues using JQL.

        Args:
            jql (str): A valid JQL query.

        Returns:
            list: Returns a list of isses.
        """
        start_at = 0
        issues = []
        total = 1
        while len(issues) < total:
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
            data = self.__get('search', params={'jql': jql, 'startAt': start_at}).json()
            total = data['total']
            issues.extend(data['issues'])
            start_at += len(data['issues'])
        return issues

    def create_issue(self, fields: dict) -> dict:
        """Create an issue in Jira.

        Args:
            fields (dict): Fields to populate the new Jira issue.

        Returns:
            dict: Information about the newly created issue such as: id, key, and self.
        """
        # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post
        return self.__post('issue', body={'fields': fields}).json()

    def add_text_comment(self, issue_id_or_key, comment: str, is_internal: bool = True) -> dict:
        """Add a *text* comment to a Jira issue. The reason for the emphasis on "text" is because the format that Atlassian expects for special formatting is crazy and I don't want to figure it out.

        If you want, you can read about the Atlassian Document Format here: https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/

        Args:
            issue_id_or_key (int or str): The key or id of the issue where teh comment will be added.
            comment (str): The comment.
            is_internal (bool, optional): Whether or not the comment will be internal or customer visable for Jira Service Desk issues. Defaults to True.

        Returns:
            dict: Returns comment information from the API.
        """
        # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-post
        return self.__post(f'issue/{issue_id_or_key}/comment', body={
            'properties': [
                {
                    'key': 'sd.public.comment',
                    'value':
                        {
                            'internal': is_internal
                        }
                }
            ],
            'body': {
                'version': 1,
                'type': 'doc',
                'content': [
                    {
                        'type': 'paragraph',
                        'content': [
                            {
                                'type': 'text',
                                'text': comment
                            }
                        ]
                    }
                ]
            }
        }).json()

    def transition_issue(self, issue_id_or_key, transition_id: int):
        """Transition a Jira issue.

        Args:
            issue_id_or_key (int or str): The id or key of the issue that will be transitioned.
            transition_id (int): Id of the transition to be performed.
        """
        # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-post
        # Transitioning an issue returns no data, so we also return nothing.
        self.__post(f'issue/{issue_id_or_key}/transitions', body={'transition': {'id': transition_id}})

    def get_user_by_email(self, email: str) -> dict:
        """Fetch user information by searching for user email.

        Args:
            email (str): Email of desired user.

        Raises:
            ValueError: If the email returns more than one user. Atlassian does not explicitly guarantee that email is a unique user attribute.

        Returns:
            dict: Full user data from Jira Cloud.
        """
        data = self.__get('user/search', params={'query': email}).json()
        if len(data) > 1:
            raise ValueError('More than one user returned from query')
        if not data or data[0]['emailAddress'] != email:
            return {}
        return data[0]

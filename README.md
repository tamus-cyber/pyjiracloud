# pyjiracloud
Python library for interacting with Jira Cloud's API. Only API calls that we need have been implemented.

## Examples
```python
# Create Jira Object
jira = JiraCloud(atlassian_cloud_domain='example', username='user@example.com', api_token='secret')

# Search Issues
issues = jira.search_issues(jql='project = KEY and status = Closed')

# Create Issue
issue = jira.create_issue(fields={'project': {'key': 'KEY'}, 'summary': 'Howdy, world!', 'description': 'Testing'})

# Add Comment
comment = jira.add_text_comment(issue_id_or_key='KEY-123', comment='This is a comment.', is_internal=True)

# Transition Issue
jira.transition_issue(issue_id_or_key='KEY-123', transition_id=456)

# Find User
user = get_user_by_email(email='user@example.com')
```

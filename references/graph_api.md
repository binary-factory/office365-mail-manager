# Microsoft Graph API Reference

## Endpoints Used

### Authentication
```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
```

### Messages
```
GET https://graph.microsoft.com/v1.0/users/{user}/messages
POST https://graph.microsoft.com/v1.0/users/{user}/messages/{id}/move
POST https://graph.microsoft.com/v1.0/users/{user}/messages/{id}/forward
PATCH https://graph.microsoft.com/v1.0/users/{user}/messages/{id}
```

### Mail Folders
```
GET https://graph.microsoft.com/v1.0/users/{user}/mailFolders
POST https://graph.microsoft.com/v1.0/users/{user}/mailFolders
```

## Required Scopes

```
Mail.Read
Mail.ReadWrite
Mail.Send
MailboxSettings.Read
User.Read
```

## Query Parameters

### Filtering
```
$filter=isRead eq false
$filter=receivedDateTime ge 2024-01-01T00:00:00Z
$filter=from/emailAddress/address eq 'someone@example.com'
```

### Selecting Fields
```
$select=id,subject,receivedDateTime,from,isRead
```

### Ordering
```
$orderby=receivedDateTime desc
```

### Pagination
```
$top=20
$skip=20
```

## Response Format

### Message Object
```json
{
  "id": "string",
  "subject": "string",
  "bodyPreview": "string",
  "receivedDateTime": "2024-01-01T12:00:00Z",
  "isRead": false,
  "importance": "normal",
  "hasAttachments": true,
  "from": {
    "emailAddress": {
      "name": "Sender Name",
      "address": "sender@example.com"
    }
  },
  "toRecipients": [...],
  "ccRecipients": [...]
}
```

## Rate Limits

- Default: 10,000 requests per 10 minutes per user
- Burst: 100 requests per second
- Retry-After header provided on 429 responses

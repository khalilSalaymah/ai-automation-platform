# White-Label Configuration

This document describes the white-label functionality that allows organizations to customize the appearance and branding of the platform.

## Features

- **Theme Variables**: Customize colors, fonts, and styling
- **Custom Logo**: Upload and display organization logos
- **Custom Domain Mapping**: Map custom domains to organizations
- **Per-Organization Settings**: All branding settings are stored per organization

## Backend API

### Endpoints

#### Get Branding Settings
```
GET /api/branding/settings
```
Returns the current organization's branding settings.

**Response:**
```json
{
  "logo_url": "/api/branding/logo/org_123_logo.png",
  "custom_domain": "example.com",
  "theme_variables": {
    "primary_color": "#3b82f6",
    "secondary_color": "#8b5cf6",
    "accent_color": "#10b981",
    "background_color": "#ffffff",
    "text_color": "#1f2937",
    "font_family": "Inter, sans-serif",
    "font_size_base": "16px",
    "border_radius": "8px"
  }
}
```

#### Update Branding Settings
```
PUT /api/branding/settings
```

**Request Body:**
```json
{
  "custom_domain": "example.com",
  "theme_variables": {
    "primary_color": "#3b82f6",
    "secondary_color": "#8b5cf6",
    "accent_color": "#10b981",
    "background_color": "#ffffff",
    "text_color": "#1f2937",
    "font_family": "Inter, sans-serif",
    "font_size_base": "16px",
    "border_radius": "8px"
  }
}
```

#### Upload Logo
```
POST /api/branding/logo/upload
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Image file (PNG, JPEG, SVG, GIF, or WebP, max 5MB)

**Response:**
```json
{
  "logo_url": "/api/branding/logo/org_123_logo.png",
  "filename": "org_123_logo.png"
}
```

#### Get Logo
```
GET /api/branding/logo/{filename}
```
Public endpoint to retrieve logo files.

#### Delete Logo
```
DELETE /api/branding/logo
```
Deletes the organization's logo.

## Database Schema

The `Organization` model has been extended with the following fields:

```python
class Organization(SQLModel, table=True):
    # ... existing fields ...
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = Field(default=None, unique=True, index=True)
    theme_variables: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
```

## Frontend Usage

### Using the WhiteLabelConfig Component

```jsx
import { WhiteLabelConfig, useAuth } from '@ui/components';

function AdminPage() {
  const { token } = useAuth();
  const [showConfig, setShowConfig] = useState(false);
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  return (
    <>
      <button onClick={() => setShowConfig(true)}>
        Configure White-Label
      </button>
      {showConfig && (
        <WhiteLabelConfig
          apiUrl={API_URL}
          token={token}
          onClose={() => setShowConfig(false)}
        />
      )}
    </>
  );
}
```

### Automatic Theme Application

The `AuthProvider` automatically loads and applies branding settings when a user is authenticated. Theme variables are applied as CSS custom properties:

- `--color-primary`
- `--color-secondary`
- `--color-accent`
- `--color-background`
- `--color-text`
- `--font-family`
- `--font-size-base`
- `--border-radius`

### Using Theme Variables in CSS

```css
.my-button {
  background-color: var(--color-primary);
  border-radius: var(--border-radius);
  color: var(--color-text);
  font-family: var(--font-family);
}
```

### Using the useBranding Hook

```jsx
import { useBranding, useAuth } from '@ui/components';

function MyComponent() {
  const { token } = useAuth();
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const { logoUrl, customDomain, themeVariables, loading } = useBranding(API_URL, token);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {logoUrl && <img src={`${API_URL}${logoUrl}`} alt="Logo" />}
      <p>Domain: {customDomain}</p>
    </div>
  );
}
```

## Custom Domain Setup

To enable custom domain mapping:

1. Configure DNS: Point your custom domain to the platform's server
2. Update branding settings: Set the `custom_domain` field via the API
3. Configure reverse proxy: Update your nginx/ingress configuration to route the custom domain to the appropriate organization

Example nginx configuration:
```nginx
server {
    server_name example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## File Storage

Logo files are stored in a temporary directory by default:
- Location: `{tempdir}/branding_uploads/`
- Naming: `{org_id}_{uuid}.{extension}`

For production, consider:
- Using a cloud storage service (S3, GCS, Azure Blob)
- Configuring a CDN for logo delivery
- Updating the `UPLOAD_DIR` path in `branding_router.py`

## Security Considerations

1. **Logo Access**: Logo endpoints are public. Consider adding authentication if needed.
2. **File Validation**: Only image files are accepted (PNG, JPEG, SVG, GIF, WebP)
3. **File Size**: Maximum 5MB per logo
4. **Domain Validation**: Custom domains are validated for format
5. **Organization Isolation**: Users can only modify their own organization's branding

## Migration

To add white-label support to existing organizations:

```python
from core.models import Organization
from core.database import get_session

# Update existing organizations with default branding
with next(get_session()) as session:
    organizations = session.exec(select(Organization)).all()
    for org in organizations:
        if org.theme_variables is None:
            org.theme_variables = {}
        session.add(org)
    session.commit()
```

## Example Integration

See `packages/ui/src/components/WhiteLabelConfig.jsx` for a complete example of the white-label configuration UI.

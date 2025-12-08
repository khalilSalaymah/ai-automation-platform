# UI Package

Shared React components for AI agent framework.

## Components

- `ChatWidget` - WebSocket/REST chat interface
- `FileUpload` - File upload component
- `AdminLayout` - Admin dashboard layout

## Usage

```jsx
import { ChatWidget } from '@ui/components';

<ChatWidget wsUrl="ws://localhost:8081/ws" restUrl="/api/chat" />
```

## Development

```bash
npm install
npm run dev
```

## Storybook

```bash
npm run storybook
```


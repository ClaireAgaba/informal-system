# Informal System Frontend

A modular React application for the Education Management Information System (EMIS).

## Project Structure

```
src/
├── modules/                    # Feature modules (isolated and independent)
│   ├── candidates/            # Candidate management module
│   │   ├── pages/            # Page components
│   │   ├── components/       # Module-specific components
│   │   ├── services/         # API services
│   │   └── routes.jsx        # Module routes
│   ├── occupations/          # Occupation management module
│   ├── assessmentCenters/    # Assessment centers module
│   ├── users/                # User management module
│   ├── payments/             # Payment management module
│   └── reports/              # Reports module
│
├── shared/                    # Shared resources across modules
│   ├── components/           # Reusable UI components
│   ├── hooks/                # Custom React hooks
│   ├── utils/                # Utility functions
│   └── constants/            # App-wide constants
│
├── layouts/                   # Layout components
│   ├── DashboardLayout.jsx   # Main dashboard layout
│   └── AuthLayout.jsx        # Authentication layout
│
├── routes/                    # Routing configuration
│   └── AppRoutes.jsx         # Main routes
│
├── services/                  # Core services
│   └── apiClient.js          # Axios instance with interceptors
│
├── App.jsx                    # Root component
├── main.jsx                   # Application entry point
└── index.css                  # Global styles
```

## Module Architecture

Each module follows a consistent structure:

- **pages/**: Full page components (List, Create, Edit, View)
- **components/**: Module-specific reusable components
- **services/**: API calls and data fetching logic
- **routes.jsx**: Module-specific routing

### Benefits:
- ✅ **Isolation**: Modules are independent and can be developed separately
- ✅ **Maintainability**: Easy to locate and update module-specific code
- ✅ **Scalability**: Add new modules without affecting existing ones
- ✅ **Reusability**: Shared components and utilities are centralized

## Tech Stack

- **React 18** - UI library
- **React Router v6** - Routing
- **TanStack Query** - Server state management
- **Axios** - HTTP client
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Sonner** - Toast notifications
- **Vite** - Build tool

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will run on `http://localhost:3000` with API proxy to `http://127.0.0.1:8001`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Path Aliases

The following path aliases are configured for cleaner imports:

- `@/` → `src/`
- `@modules/` → `src/modules/`
- `@shared/` → `src/shared/`
- `@layouts/` → `src/layouts/`
- `@services/` → `src/services/`

### Example Usage:

```javascript
import Button from '@shared/components/Button';
import candidateApi from '@modules/candidates/services/candidateApi';
import DashboardLayout from '@layouts/DashboardLayout';
```

## API Integration

All API calls go through the centralized `apiClient` which handles:

- Base URL configuration
- Authentication tokens
- Request/response interceptors
- Error handling

### Example API Service:

```javascript
import apiClient from '@services/apiClient';

export const candidateApi = {
  getAll: (params) => apiClient.get('/candidates', { params }),
  getById: (id) => apiClient.get(`/candidates/${id}`),
  create: (data) => apiClient.post('/candidates', data),
  update: (id, data) => apiClient.put(`/candidates/${id}`, data),
  delete: (id) => apiClient.delete(`/candidates/${id}`),
};
```

## Shared Components

Reusable components are located in `src/shared/components/`:

- **Button** - Customizable button with variants
- **Card** - Card container with header, content, footer
- More components to be added...

## Constants

Application-wide constants are defined in `src/shared/constants/`:

- Registration categories
- Intake options
- Gender options
- Verification status
- Account status
- And more...

## Development Guidelines

1. **Module Independence**: Each module should be self-contained
2. **Shared Resources**: Use shared components and utilities for common functionality
3. **API Services**: Keep all API calls in service files
4. **Consistent Naming**: Follow established naming conventions
5. **Type Safety**: Use prop validation where appropriate

## Next Steps

1. Implement authentication module
2. Create candidate management pages
3. Build occupation management interface
4. Develop assessment center management
5. Add reporting functionality
6. Implement payment tracking

## License

Private - Internal Use Only

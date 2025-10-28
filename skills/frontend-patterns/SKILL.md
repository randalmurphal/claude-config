---
name: frontend-patterns
description: Frontend development patterns for React, Vue, and TypeScript including component composition, state management (Redux, Zustand, Pinia), hooks patterns, performance optimization, testing with Jest/Vitest, and build tools (Vite, webpack). Use when building frontend applications, optimizing performance, managing state, or setting up testing.
allowed-tools: [Read, Write, Bash, Grep]
---

# Frontend Patterns Skill

## Overview
This skill provides comprehensive patterns for modern frontend development including React, Vue, TypeScript, state management, performance optimization, and testing strategies.

## Component Patterns

### React Component Composition

**Functional Components (Preferred)**
```tsx
// Simple component
interface ButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({
  onClick,
  children,
  variant = 'primary'
}) => {
  return (
    <button className={`btn-${variant}`} onClick={onClick}>
      {children}
    </button>
  );
};
```

**Composition Over Inheritance**
```tsx
// Container/Presenter pattern
const UserListContainer: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    fetchUsers().then(setUsers);
  }, []);

  return <UserList users={users} />;
};

const UserList: React.FC<{ users: User[] }> = ({ users }) => (
  <ul>
    {users.map(user => <UserItem key={user.id} user={user} />)}
  </ul>
);
```

**Render Props Pattern**
```tsx
interface DataFetcherProps<T> {
  url: string;
  render: (data: T | null, loading: boolean, error: Error | null) => React.ReactNode;
}

function DataFetcher<T>({ url, render }: DataFetcherProps<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return <>{render(data, loading, error)}</>;
}
```

**Higher-Order Components (HOC)**
```tsx
function withAuth<P extends object>(
  Component: React.ComponentType<P>
): React.FC<P> {
  return (props: P) => {
    const { user } = useAuth();

    if (!user) {
      return <Redirect to="/login" />;
    }

    return <Component {...props} />;
  };
}

const ProtectedPage = withAuth(Dashboard);
```

### Vue Component Patterns

**Composition API (Vue 3)**
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface User {
  id: number;
  name: string;
}

const users = ref<User[]>([]);
const loading = ref(true);

const activeUsers = computed(() =>
  users.value.filter(u => u.active)
);

onMounted(async () => {
  users.value = await fetchUsers();
  loading.value = false;
});
</script>

<template>
  <div v-if="loading">Loading...</div>
  <ul v-else>
    <li v-for="user in activeUsers" :key="user.id">
      {{ user.name }}
    </li>
  </ul>
</template>
```

**Composables (Vue 3)**
```ts
// useUser.ts
import { ref, Ref } from 'vue';

export function useUser() {
  const user: Ref<User | null> = ref(null);
  const loading = ref(false);

  async function fetchUser(id: number) {
    loading.value = true;
    try {
      user.value = await api.getUser(id);
    } finally {
      loading.value = false;
    }
  }

  return { user, loading, fetchUser };
}

// Usage in component
const { user, loading, fetchUser } = useUser();
```

## React Hooks Patterns

### Custom Hooks

**Data Fetching Hook**
```tsx
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (mounted) setData(data);
      })
      .catch(err => {
        if (mounted) setError(err);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [url]);

  return { data, loading, error };
}
```

**Form Hook**
```tsx
interface UseFormOptions<T> {
  initialValues: T;
  validate?: (values: T) => Partial<Record<keyof T, string>>;
  onSubmit: (values: T) => void | Promise<void>;
}

function useForm<T extends Record<string, any>>({
  initialValues,
  validate,
  onSubmit
}: UseFormOptions<T>) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (validate) {
      const validationErrors = validate(values);
      setErrors(validationErrors);
      if (Object.keys(validationErrors).length > 0) return;
    }

    setSubmitting(true);
    try {
      await onSubmit(values);
    } finally {
      setSubmitting(false);
    }
  };

  return { values, errors, handleChange, handleSubmit, submitting };
}
```

**Local Storage Hook**
```tsx
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  };

  return [storedValue, setValue] as const;
}
```

## State Management Comparison

| Feature | Redux | Zustand | Pinia (Vue) | Context API |
|---------|-------|---------|-------------|-------------|
| Boilerplate | High | Low | Medium | Low |
| DevTools | Excellent | Good | Excellent | None |
| TypeScript | Good | Excellent | Excellent | Good |
| Learning Curve | Steep | Gentle | Moderate | Gentle |
| Bundle Size | ~12KB | ~1KB | ~1KB | 0KB (built-in) |
| Best For | Large apps | Medium apps | Vue apps | Simple state |

### Redux Toolkit (Modern Redux)

```tsx
// store/userSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface UserState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

const initialState: UserState = {
  user: null,
  loading: false,
  error: null
};

export const fetchUser = createAsyncThunk(
  'user/fetch',
  async (userId: number) => {
    const response = await api.getUser(userId);
    return response.data;
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchUser.fulfilled, (state, action: PayloadAction<User>) => {
        state.loading = false;
        state.user = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch user';
      });
  }
});

export const { logout } = userSlice.actions;
export default userSlice.reducer;

// Component usage
const UserProfile: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user, loading } = useAppSelector(state => state.user);

  useEffect(() => {
    dispatch(fetchUser(123));
  }, [dispatch]);

  if (loading) return <div>Loading...</div>;
  return <div>{user?.name}</div>;
};
```

### Zustand (Lightweight Alternative)

```tsx
// store/useUserStore.ts
import create from 'zustand';

interface UserStore {
  user: User | null;
  loading: boolean;
  fetchUser: (id: number) => Promise<void>;
  logout: () => void;
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  loading: false,

  fetchUser: async (id) => {
    set({ loading: true });
    try {
      const user = await api.getUser(id);
      set({ user, loading: false });
    } catch (error) {
      set({ loading: false });
    }
  },

  logout: () => set({ user: null })
}));

// Component usage (much simpler)
const UserProfile: React.FC = () => {
  const { user, loading, fetchUser } = useUserStore();

  useEffect(() => {
    fetchUser(123);
  }, [fetchUser]);

  if (loading) return <div>Loading...</div>;
  return <div>{user?.name}</div>;
};
```

### Pinia (Vue State Management)

```ts
// stores/user.ts
import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    loading: false
  }),

  getters: {
    isLoggedIn: (state) => state.user !== null,
    userName: (state) => state.user?.name || 'Guest'
  },

  actions: {
    async fetchUser(id: number) {
      this.loading = true;
      try {
        this.user = await api.getUser(id);
      } finally {
        this.loading = false;
      }
    },

    logout() {
      this.user = null;
    }
  }
});

// Component usage
<script setup>
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();
const { isLoggedIn, userName } = storeToRefs(userStore);

onMounted(() => {
  userStore.fetchUser(123);
});
</script>
```

## TypeScript Patterns

### Type-Safe Props

```tsx
// Discriminated unions for variants
type ButtonProps =
  | { variant: 'link'; href: string; onClick?: never }
  | { variant: 'button'; onClick: () => void; href?: never };

const Button: React.FC<ButtonProps> = (props) => {
  if (props.variant === 'link') {
    return <a href={props.href}>Link</a>;
  }
  return <button onClick={props.onClick}>Button</button>;
};

// Generic components
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string | number;
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map(item => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}
```

### API Types

```tsx
// Response types
interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

interface User {
  id: number;
  name: string;
  email: string;
}

// Type-safe API client
class ApiClient {
  async get<T>(url: string): Promise<ApiResponse<T>> {
    const response = await fetch(url);
    return response.json();
  }

  async post<T, D = unknown>(url: string, data: D): Promise<ApiResponse<T>> {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}

// Usage
const api = new ApiClient();
const { data: user } = await api.get<User>('/users/1');
```

## Performance Optimization

### Memoization

```tsx
// React.memo for component memoization
const ExpensiveComponent = React.memo<{ data: Data }>(({ data }) => {
  // Only re-renders if data changes
  return <div>{data.value}</div>;
}, (prevProps, nextProps) => {
  // Custom comparison (optional)
  return prevProps.data.id === nextProps.data.id;
});

// useMemo for expensive calculations
const MemoizedList: React.FC<{ items: Item[] }> = ({ items }) => {
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => a.name.localeCompare(b.name));
  }, [items]);

  return <ul>{sortedItems.map(item => <li key={item.id}>{item.name}</li>)}</ul>;
};

// useCallback for function memoization
const Parent: React.FC = () => {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []); // Function identity stable

  return <Child onClick={handleClick} />;
};
```

### Code Splitting and Lazy Loading

```tsx
// Route-based code splitting
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Suspense>
  );
}

// Component lazy loading
const HeavyComponent = lazy(() => import('./HeavyComponent'));

function Parent() {
  const [show, setShow] = useState(false);

  return (
    <div>
      <button onClick={() => setShow(true)}>Load</button>
      {show && (
        <Suspense fallback={<Spinner />}>
          <HeavyComponent />
        </Suspense>
      )}
    </div>
  );
}
```

### Virtual Lists

```tsx
// Using react-window for large lists
import { FixedSizeList } from 'react-window';

const VirtualList: React.FC<{ items: Item[] }> = ({ items }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>{items[index].name}</div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
};
```

## Testing Patterns

### Component Testing (Jest + React Testing Library)

```tsx
// UserProfile.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserProfile } from './UserProfile';

describe('UserProfile', () => {
  it('renders user name when loaded', async () => {
    const mockUser = { id: 1, name: 'John Doe' };
    jest.spyOn(api, 'getUser').mockResolvedValue(mockUser);

    render(<UserProfile userId={1} />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    await userEvent.click(screen.getByText('Click me'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Hook Testing

```tsx
// useCounter.test.ts
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('increments counter', () => {
    const { result } = renderHook(() => useCounter());

    expect(result.current.count).toBe(0);

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });
});
```

### Vitest (Modern Alternative)

```tsx
// Component.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/vue';

describe('Component', () => {
  it('renders correctly', () => {
    const { getByText } = render(Component, {
      props: { title: 'Hello' }
    });

    expect(getByText('Hello')).toBeInTheDocument();
  });
});
```

## Build Tools

### Vite Configuration

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components')
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['lodash', 'date-fns']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

### Webpack (Legacy)

```js
// webpack.config.js
module.exports = {
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash].js'
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors'
        }
      }
    }
  }
};
```

## Quick Reference

### When to Use What

**Component Patterns:**
- Composition: Default choice for most components
- Render Props: Sharing behavior across components
- HOC: Cross-cutting concerns (auth, logging)
- Hooks: Reusable stateful logic

**State Management:**
- Context API: Simple app-wide state (theme, user)
- Zustand: Medium complexity, want simplicity
- Redux: Large app, time-travel debugging needed
- Pinia: Vue applications

**Performance:**
- React.memo: Expensive components with stable props
- useMemo: Expensive calculations
- useCallback: Passing callbacks to memoized children
- Lazy loading: Route splitting, heavy components

**Testing:**
- Jest + RTL: React applications (industry standard)
- Vitest: Modern apps, faster than Jest
- Vue Test Utils: Vue applications

### Common Pitfalls

1. **Over-memoization**: Don't memo everything, measure first
2. **Prop drilling**: Use composition or context, not deep props
3. **useEffect dependencies**: Always include all dependencies
4. **Key props**: Use stable IDs, not array indices
5. **State updates**: Use functional updates when depending on previous state

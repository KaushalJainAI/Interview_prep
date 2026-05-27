# React -- Worked Code Examples

> Companion to [react-full-cheatsheet.md](react-full-cheatsheet.md). Production-shape patterns with the bug fixes interviewers love to see.

## 1. The most-asked React interview snippet -- counter with stale state
**Bug**:
```jsx
const [count, setCount] = useState(0);

// click handler
function increment3() {
  setCount(count + 1);
  setCount(count + 1);
  setCount(count + 1);
}
// Result: count goes up by 1, not 3
```
**Fix**: functional updater, which gets the latest state at apply time.
```jsx
function increment3() {
  setCount(c => c + 1);
  setCount(c => c + 1);
  setCount(c => c + 1);
}
```
**Lesson**: React batches state updates. The 3 calls all reference the same stale `count`. Functional updates queue properly.

## 2. useEffect dependency array -- the classic mistake

### Stale closure bug
```jsx
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + 1);             // captured count = 0 forever
  }, 1000);
  return () => clearInterval(id);
}, []);                              // empty deps -> effect never sees updates
```

### Two fixes
```jsx
// Option A: functional update -- no dependency on count
useEffect(() => {
  const id = setInterval(() => setCount(c => c + 1), 1000);
  return () => clearInterval(id);
}, []);

// Option B: declare the dependency and recreate interval
useEffect(() => {
  const id = setInterval(() => setCount(count + 1), 1000);
  return () => clearInterval(id);
}, [count]);                          // but this restarts interval every tick
```
Prefer Option A.

## 3. Fetching with abort on unmount

```jsx
function UserProfile({ userId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then(r => {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(setData)
      .catch(err => {
        if (err.name !== 'AbortError') setError(err);
      });
    return () => controller.abort();
  }, [userId]);

  if (error) return <Error e={error} />;
  if (!data) return <Spinner />;
  return <div>{data.name}</div>;
}
```
**Why abort**: if user navigates away or `userId` changes mid-fetch, the stale request would set state on an unmounted component -> memory leak + warning.

**Better**: use TanStack Query -- handles this + caching + retries.

## 4. Custom hook -- useDebouncedValue

```jsx
function useDebouncedValue(value, ms = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

// Usage in a search box
function Search() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (debouncedQuery) fetchResults(debouncedQuery);
  }, [debouncedQuery]);

  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```
**Logic**: every render, set a 300ms timer. If `value` changes before timer fires, the cleanup cancels and a new timer starts. Final unchanged value triggers the update.

## 5. useMemo / useCallback -- when they actually help

```jsx
function ProductList({ products, onAddToCart }) {
  //  wasted memo -- primitive comparison is already fast
  const total = useMemo(() => products.reduce((s, p) => s + p.price, 0), [products]);

  //  memoize EXPENSIVE work
  const filtered = useMemo(
    () => products.filter(p => p.active && matchesQuery(p.name, query)),
    [products, query]
  );

  //  useCallback when passing to memo'd child
  const handleClick = useCallback((id) => {
    onAddToCart(id);
  }, [onAddToCart]);

  return filtered.map(p => <Item key={p.id} product={p} onClick={handleClick} />);
}

const Item = React.memo(({ product, onClick }) => (
  <button onClick={() => onClick(product.id)}>{product.name}</button>
));
```
**Rule**: `useMemo`/`useCallback` are NOT free -- they add memory + dep-check overhead. Use only when child is `memo`-wrapped or computation is truly expensive.

## 6. Reducer for complex state -- cart example

```jsx
function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD':
      const existing = state.items.find(i => i.id === action.id);
      if (existing) {
        return { ...state,
          items: state.items.map(i =>
            i.id === action.id ? { ...i, qty: i.qty + 1 } : i),
        };
      }
      return { ...state,
        items: [...state.items, { id: action.id, qty: 1, price: action.price }],
      };
    case 'REMOVE':
      return { ...state,
        items: state.items.filter(i => i.id !== action.id),
      };
    case 'CLEAR': return { items: [] };
    default: throw new Error(`Unknown action: ${action.type}`);
  }
}

function Cart() {
  const [cart, dispatch] = useReducer(cartReducer, { items: [] });
  // ... use dispatch({type:'ADD', id, price})
}
```
**When useReducer wins over useState**: 3+ related state pieces, transitions are explicit, easy to test pure reducer in isolation.

## 7. Context + reducer = lightweight Redux

```jsx
const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cart, dispatch] = useReducer(cartReducer, { items: [] });

  // memoize so consumers don't re-render on parent re-render
  const value = useMemo(() => ({ cart, dispatch }), [cart]);
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be inside CartProvider');
  return ctx;
}
```
**`useMemo` on value**: every render of `CartProvider` creates a new object -> forces all consumers to re-render. Memoize against the state.

## 8. React Query -- replacing useEffect+useState for data

```jsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function ProductDetail({ slug }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['product', slug],
    queryFn: () => fetch(`/api/products/${slug}`).then(r => r.json()),
    staleTime: 60_000,
  });

  const queryClient = useQueryClient();
  const addToCart = useMutation({
    mutationFn: (id) => fetch('/api/cart', { method:'POST', body: JSON.stringify({id}) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cart'] }),
  });

  if (isLoading) return <Spinner />;
  if (error) return <Error e={error} />;
  return (
    <div>
      <h1>{data.name}</h1>
      <button onClick={() => addToCart.mutate(data.id)} disabled={addToCart.isPending}>
        Add to cart
      </button>
    </div>
  );
}
```
**Replaces**: dozens of lines of `useEffect`+`useState`+`useRef` boilerplate per endpoint.

## 9. Lazy loading routes

```jsx
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const Home = lazy(() => import('./Home'));
const Products = lazy(() => import('./Products'));
const Admin = lazy(() => import('./Admin'));         // big bundle, lazy loaded

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Spinner />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products/*" element={<Products />} />
          <Route path="/admin/*" element={<Admin />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```
Vite/Webpack split each dynamic `import()` into its own chunk -> initial bundle smaller.

## 10. WebSocket subscription with Zustand (the AIAAS pattern)

```jsx
import { create } from 'zustand';

export const useWorkflowStore = create((set, get) => ({
  runs: {},                           // run_id -> { nodes, status, ... }
  socket: null,

  connect(runId) {
    const ws = new WebSocket(`wss://api.aiaas/runs/${runId}`);
    ws.onmessage = (e) => {
      const event = JSON.parse(e.data);
      set(state => ({
        runs: {
          ...state.runs,
          [runId]: {
            ...state.runs[runId],
            nodes: {
              ...state.runs[runId]?.nodes,
              [event.node_id]: { status: event.status, output: event.output },
            },
          },
        },
      }));
    };
    set({ socket: ws });
  },
  disconnect() {
    get().socket?.close();
    set({ socket: null });
  },
}));

// Component
function WorkflowRun({ runId }) {
  const run = useWorkflowStore(s => s.runs[runId]);
  const connect = useWorkflowStore(s => s.connect);
  const disconnect = useWorkflowStore(s => s.disconnect);

  useEffect(() => {
    connect(runId);
    return disconnect;
  }, [runId]);

  return <Graph nodes={run?.nodes} />;
}
```
**Why Zustand over Context**: doesn't re-render every consumer on every change -- selectors target subtrees of state.

## Interview-quick answers
- *useEffect vs useLayoutEffect?* useEffect runs after paint (async). useLayoutEffect runs sync before paint -- use only when measuring DOM.
- *Why need keys in lists?* React's reconciler uses keys to match old/new elements; bad keys (index when items reorder) -> wrong DOM updates + lost state.
- *Why React.StrictMode double-renders in dev?* To surface side-effect bugs (impure renders, leftover subscriptions).
- *forwardRef when?* When a parent needs a ref to a DOM node inside a custom component.
- *useRef vs useState?* useRef changes don't trigger re-render -- use for DOM refs, mutable values that don't affect UI.
- *Server Components vs Client Components (Next.js)?* Server: render on server, zero JS shipped. Client: interactive, ships JS. Default to server in Next 13+.

# API Design Standards SOP

## Related Documentation
- `database-optimization.md` - Query patterns and caching
- `security-protocols.md` - API authentication and security
- `../system/architecture.md` - Service layer organization

---

## Overview

This SOP defines API design patterns, service layer organization, error handling, and best practices for your application.

**Key Principles:**
1. **Service Layer Pattern** - All data access goes through `/src/services/`
2. **Cache-First Architecture** - Use CacheManager for all repeated queries
3. **Consistent Error Handling** - Standardized error responses
4. **Type Safety** - TypeScript interfaces for all API responses
5. **Separation of Concerns** - UI logic separate from data fetching

---

## Service Layer Pattern

### Service Organization

**Pattern: One service per domain**

```
src/services/
├── authService.ts                  # Authentication & user management
├── sessionService.ts               # Session management
├── transactionService.ts           # Transaction operations
├── catalogService.ts               # Product catalog
├── balanceService.ts               # Balance operations
├── [verification_service].ts       # Identity verification
├── paymentService.ts               # Payment processing
├── cacheManager.ts                 # High-level cache operations
├── cacheService.ts                 # Low-level cache storage
└── catalogService.ts               # Product catalog
```

Services are organized by domain responsibility.

---

### Service Template

**Pattern: Consistent service structure**

```typescript
// ✅ CORRECT - Standard service structure
import { supabase } from '../lib/supabase';
import { cacheManager } from './cacheManager';

class CatalogService {
  private readonly CACHE_PREFIX = 'catalog';
  private readonly DEFAULT_TTL_MINUTES = 5;

  /**
   * Get catalog items with cache
   */
  async getItems(filters?: ItemFilters): Promise<Item[]> {
    const cacheKey = `${this.CACHE_PREFIX}:items:${JSON.stringify(filters)}`;

    return await cacheManager.loadWithCache(
      cacheKey,
      async () => {
        let query = supabase
          .from('[items_table]')
          .select('*, [metadata_table](*)')
          .eq('status', 'active');

        if (filters?.category) {
          query = query.eq('category', filters.category);
        }

        if (filters?.max_price) {
          query = query.lte('price_cents', filters.max_price);
        }

        const { data, error } = await query
          .order('created_at', { ascending: false })
          .limit(filters?.limit || 50);

        if (error) throw error;
        return data || [];
      },
      { ttlMinutes: this.DEFAULT_TTL_MINUTES }
    );
  }

  /**
   * Create new item
   */
  async createItem(itemData: CreateItemData): Promise<Item> {
    // 1. Validate user ownership
    const { data: existing } = await supabase
      .from('[items_table]')
      .select('id, owner_id')
      .eq('id', itemData.item_id)
      .eq('owner_id', itemData.seller_id)
      .single();

    if (!existing) {
      throw new Error('Item not found or user does not own item');
    }

    // 2. Create item
    const { data, error } = await supabase
      .from('[items_table]')
      .insert({
        seller_id: itemData.seller_id,
        item_id: itemData.item_id,
        price_cents: itemData.price_cents,
        fee_bps: 500, // 5% fee
        status: 'active',
      })
      .select('*')
      .single();

    if (error) throw error;

    // 3. Invalidate relevant caches
    await this.invalidateItemCaches(itemData.seller_id);

    return data;
  }

  /**
   * Invalidate item caches
   */
  private async invalidateItemCaches(sellerId?: string): Promise<void> {
    await cacheManager.invalidateByPrefix(`${this.CACHE_PREFIX}:items`);

    if (sellerId) {
      await cacheManager.invalidateByPrefix(`${this.CACHE_PREFIX}:seller:${sellerId}`);
    }
  }
}

export const catalogService = new CatalogService();
```

**Service Structure Guidelines:**
- **Singleton export** - Use `export const serviceName = new Service()`
- **Private properties** - Cache keys and configuration as private
- **Public methods** - Clear, typed interfaces for consumers
- **Cache management** - Wrap queries with `cacheManager.loadWithCache()`
- **Error handling** - Throw typed errors, let caller handle
- **Cache invalidation** - Invalidate affected caches on mutations

---

## Caching Strategy

### Cache-First Pattern

**All database queries MUST use cache-first pattern:**

```typescript
// ✅ CORRECT - Cache-first with TTL
const loadData = async () => {
  return await cacheManager.loadWithCache(
    'cache:key',
    async () => {
      // Database query here
      const { data, error } = await supabase.from('[table_name]').select('*');
      if (error) throw error;
      return data;
    },
    { ttlMinutes: 5 }
  );
};

// ❌ INCORRECT - Direct query without caching
const loadData = async () => {
  const { data } = await supabase.from('[table_name]').select('*');
  return data;
};
```

### Cache TTL Guidelines

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Catalog items | 5 min | Frequently changing |
| User items | 1 min | Changes on transaction |
| Account balance | 1 min | Real-time updates needed |
| Item metadata | 24 hrs | Immutable reference data |
| Product catalogs | 6 hrs | Static reference data |
| Categories, types | 1 hr | Static reference |
| User profile | 1 min | Verification status can change |

---

### Cache Invalidation Strategies

**Pattern: Invalidate on mutation**

```typescript
// ✅ CORRECT - Invalidate affected caches after mutation
const updateProfile = async (userId: string, updates: Partial<Profile>): Promise<void> => {
  // 1. Update database
  const { error } = await supabase
    .from('[profiles_table]')
    .update(updates)
    .eq('id', userId);

  if (error) throw error;

  // 2. Invalidate user-specific caches
  await cacheManager.invalidateByPrefix(`user:${userId}`);

  // 3. Invalidate related caches
  if (updates.verification_status) {
    await cacheManager.invalidateByPrefix(`verification:${userId}`);
  }
};

// Strategies:
// - invalidateByPrefix() - Clear all keys matching prefix
// - invalidateCache() - Clear specific key
// - invalidateAll() - Nuclear option, clear everything
```

---

## Error Handling

### Error Types

**Pattern: Typed error hierarchy**

```typescript
// Define error types
export class APIError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication required', details?: any) {
    super(message, 'AUTH_REQUIRED', 401, details);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends APIError {
  constructor(message: string, details?: any) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends APIError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends APIError {
  constructor(retryAfter?: number) {
    super('Rate limit exceeded', 'RATE_LIMIT', 429, { retryAfter });
    this.name = 'RateLimitError';
  }
}
```

---

### Error Handling Pattern

**Pattern: Try-catch with typed errors**

```typescript
// ✅ CORRECT - Consistent error handling
const createOrder = async (orderData: OrderData): Promise<Order> => {
  try {
    // Validation
    if (!orderData.shipping_address) {
      throw new ValidationError('Shipping address is required');
    }

    // Authentication check
    if (!authService.isAuthenticated()) {
      throw new AuthenticationError();
    }

    // Business logic
    const session = await sessionService.getSession();
    if (!session) {
      throw new APIError(
        'Session expired',
        'SESSION_EXPIRED',
        401,
        { requiresReauth: true }
      );
    }

    // API call
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { /* headers */ },
      body: JSON.stringify(orderData),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new AuthenticationError('Session invalid');
      } else if (response.status === 429) {
        throw new RateLimitError(60); // Retry after 60 seconds
      } else {
        throw new APIError(
          'Failed to create order',
          'ORDER_CREATION_FAILED',
          response.status
        );
      }
    }

    return await response.json();
  } catch (error) {
    // Log error
    console.error('[createOrder] Error:', error);

    // Re-throw typed errors
    if (error instanceof APIError) {
      throw error;
    }

    // Wrap unknown errors
    throw new APIError(
      'An unexpected error occurred',
      'UNKNOWN_ERROR',
      500,
      { originalError: error instanceof Error ? error.message : String(error) }
    );
  }
};
```

---

### UI Error Handling

**Pattern: Error boundary + user-friendly messages**

```typescript
// Component error handling
const OrderButton: React.FC = () => {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleOrder = async () => {
    try {
      setLoading(true);
      setError(null);

      await transactionService.createTransaction(orderData);

      // Success
      Alert.alert('Success', 'Order created!');
    } catch (error) {
      // Convert technical errors to user-friendly messages
      if (error instanceof AuthenticationError) {
        setError('Please log in to create orders');
      } else if (error instanceof ValidationError) {
        setError(error.message); // Already user-friendly
      } else if (error instanceof RateLimitError) {
        setError('Too many requests. Please wait a moment and try again.');
      } else if (error instanceof APIError && error.code === 'SESSION_EXPIRED') {
        setError('Your session has expired. Please log in again.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }

      console.error('[OrderButton] Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button onPress={handleSubmit} disabled={loading}>
        {loading ? 'Creating...' : 'Create Order'}
      </Button>
      {error && <ErrorText>{error}</ErrorText>}
    </>
  );
};
```

---

## TypeScript Patterns

### Type Definitions

**Pattern: Centralized type exports**

```typescript
// src/types/index.ts - Common types
export interface UserProfile {
  id: string;
  user_id: string;
  external_id: string;
  display_name: string;
  avatar: string | null;
  verification_status: 'pending' | 'verified' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface Item {
  id: string;
  seller_id: string;
  item_id: string;
  price_cents: number;
  fee_bps: number;
  status: 'active' | 'sold' | 'cancelled' | 'reserved';
  created_at: string;
}

// src/types/catalog.ts - Domain-specific types
export interface ItemFilters {
  category?: string;
  min_price?: number;
  max_price?: number;
  condition?: string;
  brand?: string;
  limit?: number;
}

export interface CreateItemData {
  seller_id: string;
  item_id: string;
  price_cents: number;
}

// src/types/supabase.ts - Database types (auto-generated)
export interface Database {
  public: {
    Tables: {
      [table_name]: {
        Row: UserProfile;
        Insert: Omit<UserProfile, 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Omit<UserProfile, 'id'>>;
      };
      // ... more tables
    };
  };
}
```

---

### Service Method Signatures

**Pattern: Typed inputs and outputs**

```typescript
// ✅ CORRECT - Clear type signatures
class BalanceService {
  async getBalance(userId: string): Promise<AccountBalance> {
    // Implementation
  }

  async deposit(userId: string, amountCents: number): Promise<Transaction> {
    // Implementation
  }

  async withdraw(
    userId: string,
    amountCents: number,
    destination: WithdrawalDestination
  ): Promise<Transaction> {
    // Implementation
  }
}

// Types
interface AccountBalance {
  available_cents: number;
  pending_cents: number;
  currency: string;
}

interface Transaction {
  id: string;
  account_id: string;
  tx_type: 'deposit' | 'withdrawal' | 'purchase' | 'payout';
  amount_cents: number;
  balance_after_cents: number;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
}

interface WithdrawalDestination {
  type: 'bank_account' | 'debit_card';
  account_id: string;
}
```

---

## API Response Formats

### Success Response

**Pattern: Consistent structure**

```typescript
// ✅ CORRECT - Standard success response
interface APIResponse<T> {
  success: true;
  data: T;
  metadata?: {
    timestamp: string;
    cached?: boolean;
    ttl?: number;
  };
}

// Example
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "name": "Catalog Listing",
    // ... other fields
  },
  "metadata": {
    "timestamp": "2025-10-12T23:45:00Z",
    "cached": true,
    "ttl": 300
  }
}
```

---

### Error Response

**Pattern: Detailed error information**

```typescript
// ✅ CORRECT - Standard error response
interface APIErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
    timestamp: string;
  };
}

// Example
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid profile URL format",
    "details": {
      "field": "buyer_profile_url",
      "provided": "invalid-url",
      "expected": "https://example.com/profile/?id=..."
    },
    "timestamp": "2025-10-12T23:45:00Z"
  }
}
```

---

## Performance Guidelines

### Query Optimization

```typescript
// ✅ CORRECT - Optimized query with selective fields
const getItems = async (): Promise<Item[]> => {
  const { data } = await supabase
    .from('[items_table]')
    .select(`
      id,
      price_cents,
      status,
      [related_table] (
        id,
        name,
        category,
        [metadata_table] (
          image_url,
          condition,
          brand
        )
      )
    `)
    .eq('status', 'active')
    .eq('[related_table].category', 'electronics')
    .limit(50);

  return data || [];
};

// ❌ INCORRECT - Over-fetching with wildcard
const getItems = async (): Promise<Item[]> => {
  const { data } = await supabase
    .from('[items_table]')
    .select('*, [related_table](*), [metadata_table](*)');

  return data || [];
};
```

---

### Pagination

```typescript
// ✅ CORRECT - Efficient pagination
const getItemsPaginated = async (
  page: number,
  pageSize: number = 50
): Promise<PaginatedResponse<Item>> => {
  const start = page * pageSize;
  const end = start + pageSize - 1;

  const { data, error, count } = await supabase
    .from('[items_table]')
    .select('*', { count: 'exact' })
    .eq('status', 'active')
    .range(start, end);

  if (error) throw error;

  return {
    data: data || [],
    pagination: {
      page,
      pageSize,
      totalItems: count || 0,
      totalPages: Math.ceil((count || 0) / pageSize),
      hasNext: end < (count || 0),
      hasPrev: page > 0,
    },
  };
};
```

---

## Testing Guidelines

### Service Testing

```typescript
// Example service test structure
describe('CatalogService', () => {
  beforeEach(() => {
    // Clear caches
    cacheManager.invalidateAll();
  });

  describe('getItems', () => {
    it('should return active items', async () => {
      const items = await catalogService.getItems();

      expect(items).toBeDefined();
      expect(items.length).toBeGreaterThan(0);
      expect(items[0].status).toBe('active');
    });

    it('should use cache on second call', async () => {
      // First call (cache miss)
      const items1 = await catalogService.getItems();

      // Second call (cache hit)
      const items2 = await catalogService.getItems();

      expect(items1).toEqual(items2);
      // Verify cache was used (check logs or mock)
    });

    it('should filter by category', async () => {
      const electronics = await catalogService.getItems({ category: 'electronics' });

      expect(electronics.every(item => item.category === 'electronics')).toBe(true);
    });
  });

  describe('createItem', () => {
    it('should create item for owned resource', async () => {
      const item = await catalogService.createItem({
        seller_id: testUserId,
        item_id: testItemId,
        price_cents: 1000,
      });

      expect(item.id).toBeDefined();
      expect(item.price_cents).toBe(1000);
    });

    it('should throw error for non-owned resource', async () => {
      await expect(
        catalogService.createItem({
          seller_id: testUserId,
          item_id: otherUserItemId,
          price_cents: 1000,
        })
      ).rejects.toThrow('does not own item');
    });
  });
});
```

---

## Quick Reference

### Service Checklist

When creating a new service:

- [ ] Define TypeScript interfaces for inputs/outputs
- [ ] Implement caching with appropriate TTL
- [ ] Add error handling with typed errors
- [ ] Invalidate affected caches on mutations
- [ ] Document public methods with JSDoc
- [ ] Export as singleton instance
- [ ] Add unit tests

### API Call Checklist

When adding a new API call:

- [ ] Wrap in `cacheManager.loadWithCache()` if read operation
- [ ] Set appropriate TTL based on data volatility
- [ ] Handle all error cases (401, 403, 404, 429, 500)
- [ ] Validate inputs before making request
- [ ] Log errors with context
- [ ] Invalidate caches if mutation
- [ ] Return typed response
- [ ] Add loading states in UI

---

## Deep Link Redirect Handlers

### Payment Return Flow Pattern

**When to use:** External payment flows (Stripe Checkout, PayPal, etc.) that redirect users back to your app after completion.

**Problem:** Stripe redirects to HTTPS URLs (e.g., `https://your-backend.com/ios-payment/ach-success`), but iOS requires `yourapp://` deep link scheme to return to app. Without backend handling, users see 404 errors.

**Solution:** Backend HTTP 302 redirect handlers that bridge HTTPS → deep link gap.

**Implementation:**

1. **Accept HTTPS callback from payment provider:**
   ```go
   // Go server handler
   func (s *Server) handleIOSACHSuccess(w http.ResponseWriter, r *http.Request) {
       // Extract query parameters (preserve all for frontend)
       sessionID := r.URL.Query().Get("session_id")

       // Validate presence
       if sessionID == "" {
           s.logger.Warn("missing session_id in ACH success redirect")
           s.sendErrorResponse(w, http.StatusBadRequest, "session_id is required")
           return
       }

       // Construct deep link URL
       deepLink := fmt.Sprintf("yourapp://ios-payment/ach-success?session_id=%s", sessionID)

       // Structured logging
       s.logger.Info("ACH payment success redirect",
           "session_id", sessionID,
           "deep_link", deepLink,
           "payment_method", "ach",
           "platform", "ios",
           "user_agent", r.UserAgent())

       // Redirect to app via deep link
       http.Redirect(w, r, deepLink, http.StatusTemporaryRedirect)
   }
   ```

2. **Register routes for all payment methods × platforms:**
   ```go
   // Route registration in setupRoutes()

   // ACH payment redirects
   s.router.HandleFunc("/ios-payment/ach-success", s.handleIOSACHSuccess).Methods("GET")
   s.router.HandleFunc("/ios-payment/ach-cancel", s.handleIOSACHCancel).Methods("GET")
   s.router.HandleFunc("/payment/ach-success", s.handleWebACHSuccess).Methods("GET")
   s.router.HandleFunc("/payment/ach-cancel", s.handleWebACHCancel).Methods("GET")

   // Crypto payment redirects
   s.router.HandleFunc("/ios-payment/crypto-success", s.handleIOSCryptoSuccess).Methods("GET")
   s.router.HandleFunc("/ios-payment/crypto-cancel", s.handleIOSCryptoCancel).Methods("GET")
   s.router.HandleFunc("/payment/crypto-success", s.handleWebCryptoSuccess).Methods("GET")
   s.router.HandleFunc("/payment/crypto-cancel", s.handleWebCryptoCancel).Methods("GET")
   ```

3. **Configure frontend to construct backend URLs:**
   ```typescript
   // stripePaymentService.ts
   const createCheckoutSession = async (amount: number): Promise<string> => {
       const platform = Platform.OS; // 'ios', 'android', or 'web'
       const paymentMethod = 'ach'; // or 'crypto', 'card'

       // Construct success URL pointing to backend
       const successUrl = `${BACKEND_API_URL}/${platform}-payment/${paymentMethod}-success?session_id={CHECKOUT_SESSION_ID}`;
       const cancelUrl = `${BACKEND_API_URL}/${platform}-payment/${paymentMethod}-cancel?session_id={CHECKOUT_SESSION_ID}`;

       // Stripe will replace {CHECKOUT_SESSION_ID} with actual session ID
       return await createStripeSession({
           success_url: successUrl,
           cancel_url: cancelUrl,
           // ...other params
       });
   };
   ```

4. **Frontend deep link handler (already in place):**
   ```typescript
   // App.tsx handleDeepLink function
   const handleDeepLink = async (url: string) => {
       if (url.includes('ios-payment/ach-success')) {
           // Extract session_id from URL
           const sessionId = url.match(/session_id=([^&]+)/)?.[1];

           // Verify payment status
           await stripePaymentService.handlePaymentReturn(url);

           // Show success message
           Alert.alert('Bank Account Connected!', 'Your deposit is processing (4-7 days)');

           // Cleanup
           await AsyncStorage.removeItem('pending_ach_deposit');
       }
   };
   ```

**Key Design Decisions:**

- **HTTP 302 (Temporary Redirect)** - Correct status for payment redirects (not permanent)
- **Preserve all query parameters** - Frontend may need additional data beyond session_id
- **No session validation on redirect** - Let frontend/Stripe API validate, better error UX
- **Structured logging** - Include payment_method, platform, user_agent for analytics
- **Error handling for missing params** - Return 400 with JSON error, don't silently fail

**Testing:**

```bash
# Test redirect with curl
curl -v "http://localhost:8080/ios-payment/ach-success?session_id=cs_test_abc123"

# Expected response:
# HTTP/1.1 302 Temporary Redirect
# Location: yourapp://ios-payment/ach-success?session_id=cs_test_abc123

# Test missing parameter
curl -v "http://localhost:8080/ios-payment/ach-success"

# Expected response:
# HTTP/1.1 400 Bad Request
# {"error":{"message":"session_id is required","code":400}}
```

**Files:**
- Backend: Payment server main.go (redirect handlers)
- Frontend: `src/services/[payment_service].ts` (URL construction)
- Deep link handler: `App.tsx` (deep link handling)

**Reference:** Task [TASK-ID], Commit [pending]

**Why HTTPS → Deep Link Pattern:**
- **Server-side analytics** - Log payment completions, user agents, timestamps
- **Future webhook coordination** - Backend can confirm webhook received before redirect
- **Universal links fallback** - Could serve HTML page if app not installed
- **Rate limit protection** - Backend can throttle malicious redirect attempts

**Alternative (not used):** Setting `success_url` directly to `yourapp://...` would bypass backend, losing analytics and validation opportunities.

---

## Related SOPs

- `database-optimization.md` - Query patterns and performance
- `security-protocols.md` - API authentication and authorization
- `deployment-checklist.md` - API endpoint verification before deploy

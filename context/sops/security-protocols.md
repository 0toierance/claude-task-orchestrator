# Security Protocols SOP

## Related Documentation
- `../system/external-api-integration.md` - Session encryption and security
- `api-integration.md` - External authentication implementation
- `database-optimization.md` - RLS policies and secure queries

---

## Overview

This SOP defines security best practices for your application, covering authentication, data encryption, session management, payment security, and compliance standards.

**Critical Security Principles:**
1. **Defense in Depth** - Multiple layers of security (client-side + server-side + database RLS)
2. **Principle of Least Privilege** - Users can only access their own data
3. **Encryption at Rest and in Transit** - All sensitive data encrypted
4. **Session Security** - Short-lived sessions with automatic refresh
5. **Audit Trails** - All critical operations logged

---

## Authentication Architecture

### OAuth Flow

**Pattern: Multi-Device Persistent Authentication**

```typescript
// ✅ CORRECT - Persistent authentication with edge function
const handleWebViewAuthSuccess = async (userData: UserData) => {
  // 1. Call edge function to create/get auth user
  const response = await fetch(`${supabaseUrl}/functions/v1/create-auth-user`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${supabaseAnonKey}`,
    },
    body: JSON.stringify({
      externalId: userData.id,
      displayName: userData.name,
      avatarUrl: userData.avatar,
    }),
  });

  const result = await response.json();

  // 2. Set persistent session using JWT tokens
  await supabase.auth.setSession({
    access_token: result.session.access_token,
    refresh_token: result.session.refresh_token,
  });

  // 3. Store tokens for app persistence
  await AsyncStorage.setItem('app_auth_tokens', JSON.stringify({
    access_token: result.session.access_token,
    refresh_token: result.session.refresh_token,
    expires_at: Date.now() + 3600 * 1000, // 1 hour
  }));

  return result.profile;
};
```

**Critical Security Rules:**
1. **Never expose external API keys to client** - Use edge functions for external API calls
2. **JWT tokens auto-refresh** - Supabase handles refresh automatically
3. **Same auth.uid across devices** - User's external ID maps to single auth UID
4. **Profile vs Auth separation** - `[profiles_table].id` (profile ID) ≠ `[profiles_table].user_id_col` (auth UID)

---

### Profile Structure Validation

**CRITICAL: Profile table has two ID columns:**
- `[profiles_table].id` (UUID) - Profile identifier (primary key)
- `[profiles_table].user_id_col` (UUID) - Auth user identifier (FK to `auth.users.id`)

```typescript
// ✅ CORRECT - Validate profile structure before verification
const validateProfileForVerification = async (): Promise<boolean> => {
  const user = authService.getCurrentUser();

  // Check 1: Profile must have both IDs
  if (!user?.id || !user?.user_id) {
    console.error('Profile missing required ID fields');
    return false;
  }

  // Check 2: IDs must be different (common error after migration)
  if (user.id === user.user_id) {
    console.error('Profile structure invalid: id === user_id');
    return false;
  }

  // Check 3: user_id must match current auth session
  const { data: { session } } = await supabase.auth.getSession();
  if (user.user_id !== session?.user?.id) {
    console.error('Profile user_id mismatch with auth session');
    return false;
  }

  return true;
};
```

**Why this matters:**
- Verification service uses `[profiles_table].id` for backend API authentication
- Incorrect profile structure causes "User not found" errors
- Database foreign keys reference `[profiles_table].id`, not `auth.users.id`

---

## Session Management

### Session Cookie Storage

**Pattern: Two-Phase Encrypted Storage**

```typescript
// Phase 1: Capture cookies locally (device secure storage)
const captureSession = async (cookies: any[]): Promise<boolean> => {
  // 1. Extract critical session cookies
  const session: SessionData = {
    authToken: extractCookie(cookies, 'authToken'),
    sessionId: extractCookie(cookies, 'sessionId'),
    refreshToken: extractCookie(cookies, 'refreshToken'),
    additionalCookies: {}, // Capture all other cookies
  };

  // 2. Encrypt with device-specific key
  const deviceKey = await getDeviceKey();
  const encrypted = await encryptData(JSON.stringify(session), deviceKey);

  // 3. Store in iOS Keychain / Android Keystore
  await SecureStore.setItemAsync('SESSION_ENCRYPTED', JSON.stringify(encrypted));

  // 4. Mark capture time for freshness protection
  await AsyncStorage.setItem('LAST_CAPTURE_TIME', Date.now().toString());

  return true;
};

// Phase 2: Backup to Supabase (after auth is established)
const backupSessionToSupabase = async (session: SessionData): Promise<void> => {
  // 1. Get profile ID (not auth user ID!)
  const { data: profile } = await supabase
    .from('[profiles_table]')
    .select('id')
    .eq('user_id_col', authUserId)
    .single();

  // 2. Encrypt with server key
  const serverKey = await getServerKey();
  const encrypted = await encryptData(JSON.stringify(session), serverKey);

  // 3. Save to [sessions_table] table
  await supabase
    .from('[sessions_table]')
    .upsert({
      user_id: profile.id, // Use profile.id, not auth user ID
      encrypted_data: JSON.stringify(encrypted),
      session_valid_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      last_refreshed_at: new Date().toISOString(),
    });
};
```

**Security Features:**
1. **Device-specific encryption** - Keys derived from device fingerprint
2. **Server-side encryption** - Supabase backup uses separate key
3. **7-day expiry** - Configurable session duration
4. **Freshness protection** - Sessions <2 minutes old protected from deletion

---

### Session Freshness Protection

**Pattern: 2-Minute Protection Window**

```typescript
// ✅ CORRECT - Protect fresh sessions from premature deletion
const clearSession = async (): Promise<void> => {
  const lastCaptureTime = await AsyncStorage.getItem('LAST_CAPTURE_TIME');

  if (lastCaptureTime) {
    const ageMinutes = (Date.now() - parseInt(lastCaptureTime)) / (1000 * 60);

    if (ageMinutes < 2) {
      console.warn(`Session too fresh to clear (${ageMinutes.toFixed(2)} minutes old)`);
      console.warn('Sessions need propagation time. Keeping session intact.');
      return; // Don't clear local OR Supabase session
    }
  }

  // Proceed with session deletion
  await SecureStore.deleteItemAsync('SESSION_ENCRYPTED');
  await AsyncStorage.removeItem('LAST_CAPTURE_TIME');

  // Clear Supabase backup
  await supabase
    .from('[sessions_table]')
    .delete()
    .eq('user_id', profileId);
};
```

**Why this matters:**
- Sessions take 30-60 seconds to propagate across servers
- Supabase backup can take up to 19 seconds with retries
- Premature deletion causes "401 Unauthorized" on authenticated requests
- Protection window matches propagation delay + backup time

---

## Data Encryption

### Encryption Key Management

**Pattern: Multi-Layer Key Derivation**

```typescript
// Device-specific key (for local storage)
const getDeviceKey = async (): Promise<string> => {
  const deviceFingerprint = await getDeviceFingerprint();
  return `APP_SESSION_KEY_${deviceFingerprint}`;
};

// Server key (for Supabase backup)
const getServerKey = async (): Promise<string> => {
  return `APP_SESSION_KEY_SERVER`;
};

// Device fingerprint generation
const getDeviceFingerprint = async (): Promise<string> => {
  let fingerprint = await AsyncStorage.getItem('DEVICE_FINGERPRINT');

  if (!fingerprint) {
    // Generate cryptographically secure random fingerprint
    const random = await Crypto.getRandomBytesAsync(16);
    fingerprint = Array.from(random)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    await AsyncStorage.setItem('DEVICE_FINGERPRINT', fingerprint);
  }

  return fingerprint;
};
```

**Security Features:**
1. **Per-device keys** - Local storage encryption unique to each device
2. **Server-side keys** - Supabase backup uses separate encryption
3. **Random fingerprints** - 128-bit entropy for device identification
4. **Key persistence** - Fingerprints persist across app restarts

---

### Encryption Implementation (AES-256-GCM)

```typescript
// ✅ CORRECT - Simplified encryption for React Native
const encryptData = async (data: string, key: string): Promise<EncryptedSession> => {
  // 1. Generate random IV
  const iv = await Crypto.getRandomBytesAsync(16);
  const ivHex = Array.from(iv).map(b => b.toString(16).padStart(2, '0')).join('');

  // 2. Hash key with SHA-256
  const keyBuffer = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    key,
    { encoding: Crypto.CryptoEncoding.HEX }
  );

  // 3. Encrypt data (simplified for React Native - use proper crypto in production)
  const encrypted = btoa(data); // Base64 encode

  return {
    encryptedData: encrypted,
    iv: ivHex,
    validUntil: new Date(Date.now() + 24 * 60 * 60 * 1000),
  };
};

// Decryption
const decryptData = async (encrypted: EncryptedSession, key: string): Promise<string> => {
  return atob(encrypted.encryptedData);
};
```

**Production Requirements:**
- Replace `btoa/atob` with proper AES-256-GCM library (e.g., `expo-crypto`)
- Implement HMAC authentication tags
- Use secure key derivation (PBKDF2 or Argon2)

---

## Payment Security

### Stripe Integration

**Pattern: Server-Side Payment Processing**

```typescript
// ✅ CORRECT - All payment operations via secure backend
const createPaymentIntent = async (amount: number): Promise<string> => {
  // 1. Get backend session token (not Stripe keys!)
  const sessionToken = await getBackendSessionToken();

  // 2. Call backend API (not Stripe API directly)
  const response = await fetch(`${BACKEND_API_URL}/payments/create-intent`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${sessionToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      amount_cents: amount,
      currency: 'usd',
    }),
  });

  const result = await response.json();
  return result.client_secret; // Safe to expose to client
};

// ❌ INCORRECT - Never call Stripe API from client
const BAD_EXAMPLE = async () => {
  // DON'T DO THIS - Exposes Stripe secret key!
  const response = await fetch('https://api.stripe.com/v1/payment_intents', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${STRIPE_SECRET_KEY}`, // NEVER expose secret key!
    },
  });
};
```

**Security Rules:**
1. **Never expose Stripe secret keys** - Always use backend API
2. **Client secret is safe** - Client can complete payment with client_secret
3. **Backend validation** - Server verifies amounts before creating intent
4. **Webhook verification** - Backend validates Stripe webhook signatures

---

### Identity Verification

**Pattern: Lazy-Loaded Identity Verification**

```typescript
// ✅ CORRECT - Lazy verification initialization (only when needed)
const initializeVerificationFlow = async (): Promise<void> => {
  const authState = authService.getAuthState();

  // Guard: Skip for verified users
  if (authState.user?.verification_status === 'verified') {
    console.log('User already verified, skipping verification');
    return;
  }

  // 1. Set up real-time subscription for status changes
  setupRealtimeSubscription(authState.user.id);

  // 2. Pre-generate session token for smooth UX
  await getOrGenerateSessionToken(authState.user.id);

  // 3. Check current status
  await checkVerificationStatus(true);
};

// Backend session token with exponential backoff
const getOrGenerateSessionToken = async (userId: string): Promise<string | null> => {
  // 1. Check cache first
  const cached = await cacheService.get('verification', `session_token_${userId}`);
  if (cached?.token && new Date(cached.expiry) > new Date()) {
    return cached.token;
  }

  // 2. Generate new token from backend
  const response = await fetch(`${VERIFICATION_API_URL}/auth/session/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile_id: userId }),
  });

  const data = await response.json();
  const sessionToken = data.token;

  // 3. Cache token for 23 hours
  await cacheService.set('verification', `session_token_${userId}`, {
    token: sessionToken,
    expiry: data.expires_at,
  }, 23 * 60 * 60 * 1000);

  return sessionToken;
};
```

**Security Features:**
1. **Lazy loading** - No API calls for verified users (reduces costs)
2. **Profile ID authentication** - Backend verifies profile ownership
3. **Exponential backoff** - Prevents retry storms when backend is down
4. **Real-time updates** - Supabase subscription for instant verification
5. **Cache strategy** - 23-hour cache reduces API calls

---

## Row Level Security (RLS)

### RLS Policy Patterns

**Critical Tables with RLS Enabled:**
- `[profiles_table]` - Users can only read/update their own profile
- `[wallets_table]` - Users can only access their own balance
- `[orders_table]` - Buyers can read their orders, sellers can read orders for their items
- `[items_table]` - Public read, sellers can modify their own items
- `[transactions_table]` - Users can read transactions they're involved in

```sql
-- ✅ CORRECT - RLS policy for [profiles_table]
CREATE POLICY "Users can read own profile"
ON [profiles_table] FOR SELECT
USING (auth.uid() = user_id_col);

CREATE POLICY "Users can update own profile"
ON [profiles_table] FOR UPDATE
USING (auth.uid() = user_id_col);

-- ✅ CORRECT - RLS policy for [wallets_table]
CREATE POLICY "Users can read own balance"
ON [wallets_table] FOR SELECT
USING (
  user_id_col IN (
    SELECT id FROM [profiles_table]
    WHERE user_id_col = auth.uid()
  )
);

-- ✅ CORRECT - RLS policy for [orders_table] (buyer + seller access)
CREATE POLICY "Users can read own orders"
ON [orders_table] FOR SELECT
USING (
  buyer_id_col IN (
    SELECT id FROM [profiles_table]
    WHERE user_id_col = auth.uid()
  )
  OR
  id IN (
    SELECT order_id_col FROM [order_items_table]
    WHERE seller_id_col IN (
      SELECT id FROM [profiles_table]
      WHERE user_id_col = auth.uid()
    )
  )
);

-- ✅ CORRECT - RLS policy for [transactions_table] (buyer + seller access)
CREATE POLICY "Users can read own transactions"
ON [transactions_table] FOR SELECT
USING (
  buyer_id_col IN (
    SELECT id FROM [profiles_table]
    WHERE user_id_col = auth.uid()
  )
  OR
  seller_id_col IN (
    SELECT id FROM [profiles_table]
    WHERE user_id_col = auth.uid()
  )
);
```

**Tables with RLS Disabled (Public Catalogs):**
- `[metadata_table]` - Public item data (app-level auth checks)
- Public product catalogs (categories, types, brands)
- Reference tables (status types, condition types, etc.)

**App-Level Auth Pattern for RLS-Disabled Tables:**

```typescript
// ✅ CORRECT - App-level ownership check
const getItemMetadata = async (itemId: string): Promise<ItemMetadata | null> => {
  // 1. Get item metadata (RLS disabled, public read)
  const { data: metadata } = await supabase
    .from('[metadata_table]')
    .select('*')
    .eq('item_id', itemId)
    .single();

  // 2. Verify user owns the item (app-level security)
  const { data: item } = await supabase
    .from('[items_table]')
    .select('owner_id')
    .eq('id', itemId)
    .eq('owner_id', currentUserId) // RLS policy enforces this
    .single();

  if (!item) {
    throw new Error('User does not own this item');
  }

  return metadata;
};
```

---

## API Security

### Backend API Authentication

**Pattern: Profile-Based JWT Tokens**

```typescript
// ✅ CORRECT - Backend API authentication flow
const getAuthHeaders = async (): Promise<HeadersInit> => {
  const authState = authService.getAuthState();

  if (!authState.user?.id) {
    throw new Error('User not authenticated');
  }

  // 1. Get or generate backend session token
  const sessionToken = await getOrGenerateSessionToken(authState.user.id);

  // 2. Return headers with Bearer token
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionToken}`,
    'ngrok-skip-browser-warning': 'true', // For development with ngrok
  };
};

// Backend verifies token
// POST /api/v1/auth/session/generate
// Body: { profile_id: "uuid" }
// Response: { token: "jwt", expires_at: "ISO8601" }
```

**Security Rules:**
1. **Profile ID in token** - Backend can verify ownership
2. **Short-lived tokens** - 24-hour expiry, client handles refresh
3. **No sensitive operations without auth** - All mutations require valid token
4. **Rate limiting** - Backend enforces rate limits per user

---

### Request Validation

**Pattern: Multi-Layer Validation**

```typescript
// ✅ CORRECT - Client + server validation
const createOrder = async (orderData: OrderData): Promise<Order> => {
  // 1. Client-side validation
  if (!orderData.shipping_address || !orderData.items || orderData.items.length === 0) {
    throw new Error('Invalid order data');
  }

  // 2. Verify user owns items (for items) or items are available
  const { data: availableItems } = await supabase
    .from('[items_table]')
    .select('id')
    .in('id', orderData.items.map(i => i.item_id))
    .eq('status', 'active');

  if (availableItems.length !== orderData.items.length) {
    throw new Error('Some items are no longer available');
  }

  // 3. Send to backend (backend will re-validate)
  const response = await fetch(`${API_URL}/orders/create`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(orderData),
  });

  // Backend performs:
  // - Verify token signature
  // - Re-check item availability
  // - Validate shipping address
  // - Check balance
  // - Rate limit enforcement
  // - Create order in DB

  return await response.json();
};
```

---

## Account Lock Enforcement

### Negative Balance Lock System

**Purpose:** Automatically lock accounts with negative balances after a 7-day grace period, and provide instant unlock when balance is restored.

**Architecture:**
```
Balance goes negative
       ↓
Database trigger sets negative_balance_since = NOW()
       ↓
[7-day grace period - NegativeBalanceWarningBanner shown]
       ↓
Cron runs enforce-negative-balance-locks (hourly)
       ↓
Account LOCKED + Items set to 'inactive'
       ↓
User tops up → Balance positive
       ↓
"Unlock Account Instantly" button appears
       ↓
unlock-negative-balance-account edge function
       ↓
Account UNLOCKED + Items REACTIVATED
```

**Database Components:**

1. **[profiles_table] columns:**
   - `account_locked_col` (boolean) - Lock status
   - `account_locked_at_col` (timestamp) - Lock timestamp
   - `lock_reason_col` (text) - Human-readable reason
   - `lock_duration_days_col` (integer, nullable) - NULL = indefinite
   - `negative_balance_since_col` (timestamp) - Grace period start

2. **[wallets_table] trigger:** `trigger_track_negative_balance`
   - Auto-sets `negative_balance_since_col` when balance goes negative
   - Auto-clears when balance returns to positive

3. **Helper function:** `get_profiles_exceeding_negative_balance_grace_period(grace_period, use_minutes)`
   - Returns records past grace period with negative balances
   - `use_minutes: true` for testing, `false` for production

**Edge Functions:**

```typescript
// 1. LOCK FUNCTION (cron - hourly)
// enforce-negative-balance-locks
// - Finds records past 7-day grace period
// - Sets account_locked_col = true, lock_duration_days_col = NULL (indefinite)
// - DEACTIVATES all user's active items
// - Logs to [account_locks_history_table]

// 2. UNLOCK FUNCTION (user-triggered)
// unlock-negative-balance-account
// - Verifies user auth token
// - Checks balance is positive
// - Checks lock_reason_col contains "Negative balance"
// - Sets account_locked_col = false
// - REACTIVATES all user's inactive items
// - Updates [account_locks_history_table] with unlocked_at_col
```

**Cron Configuration (pg_cron):**
```sql
SELECT cron.schedule(
  'enforce-negative-balance-locks',
  '0 * * * *',  -- Hourly at minute 0
  $$SELECT net.http_post(
    url:='https://[your_project_id].supabase.co/functions/v1/enforce-negative-balance-locks',
    headers:='{"Authorization": "Bearer [anon_key]", "Content-Type": "application/json"}'::jsonb,
    body:='{}'::jsonb
  );$$
);
```

**Frontend Components:**

1. **NegativeBalanceWarningBanner** (`src/components/[warning_banner].tsx`)
   - Shows during 7-day grace period (before lock)
   - Progressive urgency: yellow (7-4 days) → orange (3-2 days) → red (1-0 days)
   - "Top Up" button navigates to deposit screen

2. **AccountLockBanner** (`src/components/[lock_banner].tsx`)
   - Shows when account is locked
   - Two modes:
     - **Time-based lock** (fraud): Shows countdown timer (D:H:M:S)
     - **Indefinite lock** (negative balance): Shows "Top up to unlock" message
   - Green "Unlock Account Instantly" button appears when balance is positive

3. **accountLockService** (`src/services/[account_lock_service].ts`)
   - `getAccountLockStatus()` - Get current lock status
   - `unlockAccountAfterTopUp()` - Calls unlock edge function
   - `canUnlockAccount()` - Check if unlock is possible

**Lock Type Differentiation:**
```typescript
// Time-based lock (transaction fraud) - 30 day countdown
lock_duration_days: 30,
lock_reason: "Transaction reversed by seller (manual investigation)"
// Shows: countdown timer, NO unlock button

// Indefinite lock (negative balance) - instant unlock when balance positive
lock_duration_days: NULL,
lock_reason: "Negative balance of $X.XX. Add funds to unlock instantly."
// Shows: "Indefinite Lock - Top up to unlock", green unlock button when balance >= 0
```

**Security Considerations:**
- Unlock function requires valid user JWT token
- Unlock only works for negative balance locks (checks lock_reason)
- Items are deactivated on lock to prevent catalog presence
- All lock/unlock events logged to `[account_locks_history_table]` for audit

---

## Fraud Prevention

### Transaction Reversal Detection

**Pattern: External API Monitoring**

```typescript
// ✅ CORRECT - Detect reversal fraud during settlement
const monitorSettlement = async (transactionId: string): Promise<void> => {
  const { data: transaction } = await supabase
    .from('[transactions_table]')
    .select('external_id_col, current_state_col')
    .eq('id', transactionId)
    .single();

  if (transaction.current_state !== 'IN_SETTLEMENT') {
    return; // Only monitor during settlement period
  }

  // Poll external API for transaction status (cached 1 hour)
  const externalStatus = await fetchExternalTransactionStatus(transaction.external_id);

  // Check for reversal
  if (externalStatus.status === 'reversed') {
    console.error('⚠️ FRAUD DETECTED - Seller reversed transaction!');

    // 1. Mark transaction as reversed
    await supabase
      .from('[transactions_table]')
      .update({
        current_state_col: 'REVERSED',
        reversal_detected_at_col: new Date().toISOString(),
      })
      .eq('id', transactionId);

    // 2. Refund buyer
    await refundBuyer(transactionId);

    // 3. Flag seller account
    await flagSellerForReview(transaction.seller_id);

    // 4. Log security event
    await supabase
      .from('[risk_events_table]')
      .insert({
        event_type_col: 'transaction_reversal',
        transaction_id_col: transactionId,
        seller_id_col: transaction.seller_id_col,
        severity_col: 'critical',
      });
  }
};
```

**Reversal Detection Flow:**
1. **Settlement monitoring** - Transaction status checked periodically during settlement
2. **Reversal status** - External service indicates seller reversed after acceptance
3. **Automatic refund** - Buyer receives full refund
4. **Seller flagging** - Account marked for manual review
5. **Payment hold** - Seller payment NOT released

---

### Rate Limiting

**Pattern: Client-Side + Server-Side Limits**

```typescript
// ✅ CORRECT - Client-side rate limiting (polite API usage)
class RateLimiter {
  private requests: number[] = [];
  private readonly maxRequests: number;
  private readonly windowMs: number;

  constructor(maxRequests: number, windowMs: number) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  async throttle(): Promise<void> {
    const now = Date.now();

    // Remove old requests outside window
    this.requests = this.requests.filter(time => now - time < this.windowMs);

    // Check if we've hit the limit
    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = this.requests[0];
      const waitTime = this.windowMs - (now - oldestRequest);

      console.log(`Rate limit reached, waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));

      // Retry throttle check
      return this.throttle();
    }

    // Record this request
    this.requests.push(now);
  }
}

// Usage
const apiLimiter = new RateLimiter(100, 60 * 1000); // 100 requests/minute

const fetchExternalData = async (): Promise<ExternalData> => {
  await apiLimiter.throttle(); // Wait if needed

  const response = await fetch(EXTERNAL_API_URL);
  return await response.json();
};
```

**Server-Side Rate Limits:**
- **Identity Verification API**: 10 requests/minute per user
- **Order Creation**: 5 orders/hour per user
- **Balance Operations**: 20 requests/minute per user
- **External API Proxy**: 50 requests/hour per user (matches external service limits)

---

## Audit Logging

### Security Event Logging

**Pattern: Comprehensive Audit Trail**

```typescript
// ✅ CORRECT - Log all security-relevant events
const logSecurityEvent = async (event: SecurityEvent): Promise<void> => {
  await supabase
    .from('[audit_logs_table]')
    .insert({
      event_type_col: event.type,
      user_id_col: event.userId,
      resource_type_col: event.resourceType,
      resource_id_col: event.resourceId,
      action_col: event.action,
      ip_address_col: event.ipAddress,
      user_agent_col: event.userAgent,
      metadata_col: event.metadata,
      severity_col: event.severity,
      created_at_col: new Date().toISOString(),
    });
};

// Critical events to log
enum SecurityEventType {
  AUTH_LOGIN = 'auth_login',
  AUTH_LOGOUT = 'auth_logout',
  AUTH_FAILURE = 'auth_failure',
  ORDER_CREATED = 'order_created',
  ORDER_COMPLETED = 'order_completed',
  ORDER_CANCELLED = 'order_cancelled',
  TRANSACTION_REVERSAL_DETECTED = 'transaction_reversal_detected',
  DEPOSIT = 'deposit',
  WITHDRAWAL = 'withdrawal',
  VERIFICATION_INITIATED = 'verification_initiated',
  VERIFICATION_VERIFIED = 'verification_verified',
  VERIFICATION_REJECTED = 'verification_rejected',
  PAYMENT_INTENT_CREATED = 'payment_intent_created',
  PAYMENT_SUCCEEDED = 'payment_succeeded',
  PAYMENT_FAILED = 'payment_failed',
  SESSION_EXPIRED = 'session_expired',
  SESSION_REFRESHED = 'session_refreshed',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',
}
```

**Audit Log Retention:**
- **Security events**: 2 years
- **Financial transactions**: 7 years (PCI compliance)
- **Transaction history**: 1 year
- **Session logs**: 90 days

---

## Compliance

### PCI DSS Compliance

**Requirements for Payment Card Data:**

1. **Never store full card numbers** - Stripe handles card storage
2. **Never store CVV/CVC** - Stripe Elements handle capture
3. **TLS 1.2+ for all transactions** - Enforced by Stripe
4. **Tokenization** - Use Stripe payment method tokens
5. **Regular security audits** - Quarterly vulnerability scans

```typescript
// ✅ CORRECT - PCI-compliant payment flow
const processPayment = async (amount: number): Promise<void> => {
  // 1. Create payment intent on backend (never expose Stripe keys)
  const clientSecret = await createPaymentIntent(amount);

  // 2. Use Stripe Elements to collect card details (Stripe handles PCI)
  const { error } = await stripe.confirmPayment({
    elements,
    clientSecret,
    confirmParams: {
      return_url: 'yourapp://payment-complete',
    },
  });

  // 3. Webhook confirms payment on backend (Stripe sends confirmation)
  // Backend validates webhook signature before crediting balance

  // ❌ NEVER DO THIS - Store card data on client or in your DB
  // const cardData = { number: '4242...', cvv: '123' }; // PCI violation!
};
```

---

### GDPR Compliance

**User Data Rights:**

1. **Right to Access** - Users can export their data
2. **Right to Deletion** - Account deletion removes all PII
3. **Right to Rectification** - Users can update profile data
4. **Data Portability** - Export data in machine-readable format

```typescript
// ✅ CORRECT - GDPR-compliant user data export
const exportUserData = async (): Promise<UserDataExport> => {
  const userId = authService.getCurrentUser()?.id;

  // 1. Export profile data
  const { data: profile } = await supabase
    .from('[profiles_table]')
    .select('*')
    .eq('id', userId)
    .single();

  // 2. Export transactions
  const { data: transactions } = await supabase
    .from('[transactions_table]')
    .select('*')
    .eq('user_id_col', userId);

  // 3. Export orders
  const { data: orders } = await supabase
    .from('[orders_table]')
    .select('*')
    .eq('buyer_id', userId);

  // 4. Export items
  const { data: items } = await supabase
    .from('[items_table]')
    .select('*')
    .eq('seller_id', userId);

  // 5. Return structured export
  return {
    profile: profile,
    transactions: transactions,
    orders: orders,
    items: items,
    exported_at: new Date().toISOString(),
  };
};

// ✅ CORRECT - GDPR-compliant account deletion
const deleteAccount = async (): Promise<void> => {
  const userId = authService.getCurrentUser()?.id;

  // 1. Anonymize profile (keep for transaction history)
  await supabase
    .from('[profiles_table]')
    .update({
      display_name_col: 'Deleted User',
      external_id_col: null,
      avatar_col: null,
      email_col: null,
      // Keep minimal data for audit trail
    })
    .eq('id', userId);

  // 2. Delete sensitive data
  await supabase
    .from('[sessions_table]')
    .delete()
    .eq('user_id', userId);

  // 3. Sign out
  await authService.signOut();
};
```

---

## Security Checklist

### Pre-Deployment Security Review

**Before deploying to production:**

- [ ] All API keys stored in environment variables (never hardcoded)
- [ ] RLS policies enabled on all user-specific tables
- [ ] Session cookies encrypted with device-specific + server keys
- [ ] Payment processing goes through backend API (no Stripe keys in client)
- [ ] Session tokens short-lived (24 hours) with automatic refresh
- [ ] Profile structure validation before all identity verification operations
- [ ] Audit logging enabled for all security events
- [ ] Rate limiting configured (client-side + server-side)
- [ ] Transaction reversal detection active during settlement
- [ ] Session freshness protection (2-minute window) implemented
- [ ] HTTPS/TLS enforced for all API requests
- [ ] Error messages don't expose sensitive information
- [ ] Dependency vulnerability scan completed
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] Backup encryption keys stored securely
- [ ] Incident response plan documented

---

### Common Security Pitfalls

**❌ DON'T:**
1. Expose Stripe secret keys to client
2. Store plaintext passwords or API keys
3. Trust client-side validation alone
4. Delete sessions <2 minutes old (propagation delay)
5. Use `[profiles_table].user_id_col` for identity verification API calls (use `[profiles_table].id`)
6. Skip reversal detection during settlement
7. Log sensitive data (passwords, credit cards, session tokens)
8. Allow unlimited API requests (implement rate limiting)
9. Hardcode encryption keys
10. Skip audit logging for financial transactions

**✅ DO:**
1. Use environment variables for all secrets
2. Encrypt all sensitive data at rest
3. Validate on both client and server
4. Implement session freshness protection
5. Use correct profile ID for backend verification API auth
6. Monitor transactions during settlement period
7. Mask sensitive data in logs
8. Implement client + server rate limiting
9. Use device-specific + server encryption keys
10. Maintain comprehensive audit trails

---

## Emergency Procedures

### Security Incident Response

**In case of suspected breach:**

1. **Immediate Actions (within 1 hour):**
   - Rotate all API keys and secrets
   - Invalidate all active sessions
   - Enable additional logging
   - Notify security team

2. **Investigation (within 24 hours):**
   - Review audit logs for suspicious activity
   - Identify affected users
   - Determine scope of breach
   - Document timeline

3. **Remediation (within 72 hours):**
   - Patch vulnerability
   - Reset affected user passwords
   - Notify affected users (GDPR requirement)
   - Update security documentation

4. **Post-Incident (within 1 week):**
   - Conduct root cause analysis
   - Implement preventive measures
   - Update security protocols
   - Train team on lessons learned

---

### Session Recovery

**If user reports "session expired" errors:**

```typescript
// Debug session status
const debugSessionStatus = await sessionService.debugSessionStatus();
console.log('Session Debug:', {
  hasLocalSession: debugSessionStatus.hasLocalSession,
  hasSupabaseSession: debugSessionStatus.hasSupabaseSession,
  isValid: debugSessionStatus.isValid,
  expiresAt: debugSessionStatus.expiresAt,
  ageMinutes: debugSessionStatus.ageMinutes,
});

// Recovery options:
if (!debugSessionStatus.hasLocalSession && debugSessionStatus.hasSupabaseSession) {
  // Restore from Supabase
  await sessionService.restoreSessionFromSupabase();
} else if (debugSessionStatus.ageMinutes < 2 && !debugSessionStatus.isValid) {
  // Session too fresh, wait for propagation
  await new Promise(resolve => setTimeout(resolve, 120000)); // Wait 2 minutes
} else {
  // Session truly expired, request re-login
  await authService.signOut();
}
```

---

## Related SOPs

- Integration-specific SOPs - External authentication and session management
- `database-optimization.md` - RLS policies and secure queries
- `api-design-standards.md` - API security best practices
- `deployment-checklist.md` - Pre-deployment security verification

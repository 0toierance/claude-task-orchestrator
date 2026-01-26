# React Native Best Practices

Standard patterns and anti-patterns for React Native development.

## Memory Management

### Rule 1: Prefer Plain Objects Over Map/Set

**Why:** React Native's V8 garbage collector has difficulty reclaiming Map and Set objects, even after references are cleared. This leads to progressive memory leaks.

**Do:**
```typescript
// ✅ Use plain objects for lookups
const lookup: Record<string, Item> = {};
items.forEach(item => {
  lookup[item.id] = item;
});

// Access
const item = lookup[itemId];

// Cleanup (optional for large objects)
// @ts-ignore
lookup = null;
```

**Don't:**
```typescript
// ❌ Maps leak in React Native
const lookup = new Map<string, Item>();
items.forEach(item => {
  lookup.set(item.id, item);
});

// Even calling clear() doesn't guarantee GC
lookup.clear();
```

**Exception:** Only use Map/Set for small (<100 items), short-lived collections where you manually call `.clear()` immediately after use.

---

### Rule 2: Explicit Cleanup for Large Objects

**Why:** V8's GC can be slow to reclaim large objects. Explicit null assignment provides a hint.

**Do:**
```typescript
async function processLargeDataset() {
  let largeObject: Record<string, any> = {};

  // ... populate with thousands of items ...

  // Process data
  await processData(largeObject);

  // Explicit cleanup hint
  // @ts-ignore
  largeObject = null;
}
```

**When to use:**
- Objects with >100 properties
- Objects containing image data or large strings
- After processing large API responses
- Before expensive operations

---

## useEffect Patterns

### Rule 3: Minimize useEffect Dependencies

**Why:** Every dependency triggers a re-run of the effect. Callback functions are recreated on every render, causing infinite re-runs.

**Do:**
```typescript
// ✅ Only stable dependencies
useEffect(() => {
  if (!enabled) return;

  let isMounted = true;

  const subscription = subscribe((data) => {
    if (!isMounted) return;
    processData(data);
  });

  return () => {
    isMounted = false;
    subscription.unsubscribe();
  };
}, [enabled]); // Only re-run when enabled changes
```

**Don't:**
```typescript
// ❌ Unstable dependencies cause re-creation
useEffect(() => {
  const subscription = subscribe(handleData);
  return () => subscription.unsubscribe();
}, [handleData, filter, options]); // Re-runs constantly!
```

**Stable Dependencies:**
- Boolean flags (`enabled`, `isActive`)
- Primitive props from parent (strings, numbers)
- useCallback with empty dependencies

**Unstable Dependencies:**
- Callback functions without useCallback
- State values that change frequently
- Objects or arrays (use JSON.stringify for comparison)
- Props that are callbacks from parent

---

### Rule 4: Always Use isMounted Pattern for Async

**Why:** Async callbacks can execute after component unmount, causing "setState on unmounted component" warnings and potential crashes.

**Do:**
```typescript
// ✅ isMounted safety pattern
useEffect(() => {
  let isMounted = true;

  async function loadData() {
    const data = await fetchData();

    // Only update state if still mounted
    if (isMounted) {
      setData(data);
    }
  }

  loadData();

  return () => {
    isMounted = false;
  };
}, []);
```

**Don't:**
```typescript
// ❌ No safety check
useEffect(() => {
  async function loadData() {
    const data = await fetchData();
    setData(data); // Crashes if unmounted!
  }

  loadData();
}, []);
```

**When to use:**
- Any async operation in useEffect
- Subscription callbacks
- setTimeout/setInterval callbacks
- Event handlers that update state
- API calls with state updates

---

### Rule 5: Comprehensive Cleanup Functions

**Why:** Leaked timers, subscriptions, and event listeners accumulate and cause memory leaks and unexpected behavior.

**Do:**
```typescript
// ✅ Comprehensive cleanup
useEffect(() => {
  let isMounted = true;
  let subscription = null;
  let intervalId = null;
  let timeoutId = null;

  // Setup
  subscription = subscribeToUpdates((data) => {
    if (!isMounted) return;
    processData(data);
  });

  intervalId = setInterval(() => {
    if (!isMounted) return;
    checkForUpdates();
  }, 5000);

  timeoutId = setTimeout(() => {
    if (!isMounted) return;
    doDelayedAction();
  }, 1000);

  return () => {
    // Comprehensive cleanup
    isMounted = false;

    if (subscription) {
      try {
        subscription.unsubscribe();
      } catch (error) {
        console.error('Cleanup error:', error);
      }
      subscription = null;
    }

    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }

    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };
}, []);
```

**Cleanup Checklist:**
- [ ] Set isMounted = false first
- [ ] Unsubscribe from all subscriptions
- [ ] Clear all intervals
- [ ] Clear all timeouts
- [ ] Remove event listeners
- [ ] Null out all refs
- [ ] Wrap each cleanup in try-catch

---

## Image Optimization

### Rule 6: Conservative Image Caching

**Why:** Caching all images in memory causes unbounded memory growth. Disk caching is sufficient for most use cases.

**Do:**
```typescript
// ✅ Disk-first caching
<CachedImage
  source={imageUrl}
  cachePolicy="disk" // Let expo-image manage memory
  priority="normal"
/>

// Only for truly immutable images
<CachedImage
  source={staticImageUrl}
  cachePolicy="memory-disk" // Static assets never change
  isStatic={true}
/>
```

**Don't:**
```typescript
// ❌ Everything in memory
<Image
  source={{ uri: imageUrl }}
  cachePolicy="memory-disk" // Unbounded memory growth!
/>
```

**Cache Policy Guidelines:**

| Cache Policy | Use Case | Memory Impact | Example |
|-------------|----------|---------------|---------|
| `memory-disk` | Immutable static assets | High | Static icons, category images |
| `disk` | User-generated, changing data | Low | Product images, user uploads, items |
| `memory` | Tiny frequently-accessed | Very Low | User avatars (<10 items) |
| `none` | Sensitive or one-time data | None | Private photos, receipts |

---

### Rule 7: Lazy Image Loading

**Why:** Loading all images immediately blocks the main thread and wastes memory for off-screen items.

**Do:**
```typescript
// ✅ Load images only when visible
<FlatList
  data={items}
  renderItem={({ item, index }) => (
    <CachedImage
      source={item.imageUrl}
      priority={index < 10 ? 'high' : 'low'} // Prioritize visible
      cachePolicy="disk"
    />
  )}
  removeClippedSubviews={true} // Unload off-screen
  initialNumToRender={10} // Only render first 10
  maxToRenderPerBatch={5} // Render 5 at a time
  windowSize={5} // Keep 5 screens worth in memory
/>
```

**Don't:**
```typescript
// ❌ Load everything immediately
<ScrollView>
  {items.map(item => (
    <Image source={{ uri: item.imageUrl }} /> // All load at once!
  ))}
</ScrollView>
```

---

## FlatList Optimization

### Rule 8: Stable Item Keys

**Why:** Unstable keys cause unnecessary re-renders and poor performance.

**Do:**
```typescript
// ✅ Stable unique keys
<FlatList
  data={items}
  keyExtractor={(item) => item.id} // Stable ID from database
  renderItem={({ item }) => <ItemCard item={item} />}
/>
```

**Don't:**
```typescript
// ❌ Unstable keys
<FlatList
  data={items}
  keyExtractor={(item, index) => index.toString()} // Changes on filter!
  keyExtractor={(item) => Math.random().toString()} // Never stable!
  renderItem={({ item }) => <ItemCard item={item} />}
/>
```

---

### Rule 9: Memoized Render Items

**Why:** FlatList re-renders items when parent re-renders unless memoized.

**Do:**
```typescript
// ✅ Memoized item component
const ItemCard = React.memo(({ item }) => {
  return (
    <View>
      <Text>{item.name}</Text>
      <CachedImage source={item.imageUrl} />
    </View>
  );
});

<FlatList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
/>
```

**Don't:**
```typescript
// ❌ Inline render - re-renders everything
<FlatList
  data={items}
  renderItem={({ item }) => (
    <View>
      <Text>{item.name}</Text>
      <Image source={{ uri: item.imageUrl }} />
    </View>
  )}
/>
```

---

### Rule 10: Virtual Scrolling Configuration

**Why:** Proper windowing prevents loading too many items in memory.

**Do:**
```typescript
// ✅ Optimized FlatList configuration
<FlatList
  data={items}
  keyExtractor={(item) => item.id}
  renderItem={RenderItem} // Memoized component

  // Performance optimizations
  removeClippedSubviews={true} // Unmount off-screen items
  maxToRenderPerBatch={10} // Render 10 at a time
  initialNumToRender={10} // Start with 10
  windowSize={5} // Keep 5 screens in memory
  updateCellsBatchingPeriod={50} // Batch updates

  // Disable expensive features if not needed
  inverted={false}
  horizontal={false}
  legacyImplementation={false}
/>
```

---

## State Management

### Rule 11: Avoid Unnecessary State

**Why:** Every state update triggers a re-render. Minimize state to minimize re-renders.

**Do:**
```typescript
// ✅ Derive values instead of storing
function ItemList({ items }) {
  const [filter, setFilter] = useState('');

  // Derive filtered items - no extra state needed
  const filteredItems = useMemo(() => {
    return items.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);

  return <FlatList data={filteredItems} />;
}
```

**Don't:**
```typescript
// ❌ Redundant state causes double re-renders
function ItemList({ items }) {
  const [filter, setFilter] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);

  useEffect(() => {
    const filtered = items.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
    setFilteredItems(filtered); // Unnecessary state update!
  }, [items, filter]);

  return <FlatList data={filteredItems} />;
}
```

---

### Rule 12: Batch State Updates

**Why:** Multiple setState calls cause multiple re-renders. Batch them when possible.

**Do:**
```typescript
// ✅ Batch related updates
async function loadData() {
  const [items, metadata, stats] = await Promise.all([
    fetchItems(),
    fetchMetadata(),
    fetchStats()
  ]);

  // Single state update
  setState(prev => ({
    ...prev,
    items,
    metadata,
    stats,
    loading: false
  }));
}
```

**Don't:**
```typescript
// ❌ Multiple re-renders
async function loadData() {
  const items = await fetchItems();
  setItems(items); // Re-render #1

  const metadata = await fetchMetadata();
  setMetadata(metadata); // Re-render #2

  const stats = await fetchStats();
  setStats(stats); // Re-render #3

  setLoading(false); // Re-render #4
}
```

---

## Debugging Patterns

### Rule 13: Render Counting

**Why:** Track component re-renders to identify performance issues.

**Pattern:**
```typescript
function useRenderCount(componentName: string) {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
    console.log(`🔄 ${componentName} render #${renderCount.current}`);
  });

  return renderCount.current;
}

// Usage
function MyComponent() {
  const renderCount = useRenderCount('MyComponent');

  return (
    <View>
      <Text>Renders: {renderCount}</Text>
    </View>
  );
}
```

---

### Rule 14: Memory Profiling

**Pattern:**
```typescript
function useMemoryMonitoring(intervalMs = 10000) {
  useEffect(() => {
    const interval = setInterval(async () => {
      const cacheSize = await Image.getCacheSize();
      const cacheMB = (cacheSize / (1024 * 1024)).toFixed(2);

      console.log(`📊 Memory: ${cacheMB}MB image cache`);

      // Add heap size monitoring in development
      if (__DEV__ && performance.memory) {
        const heapMB = (performance.memory.usedJSHeapSize / (1024 * 1024)).toFixed(2);
        console.log(`📊 Heap: ${heapMB}MB JS heap`);
      }
    }, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);
}
```

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Inline Function Props
```typescript
// Causes child re-render on every parent render
<ChildComponent onPress={() => handlePress(item.id)} />

// ✅ Use useCallback
const handleItemPress = useCallback((id) => {
  handlePress(id);
}, []);

<ChildComponent onPress={() => handleItemPress(item.id)} />
```

### ❌ Anti-Pattern 2: Creating Objects in Render
```typescript
// New object every render
<View style={{ marginTop: 10, padding: 5 }} />

// ✅ Extract to StyleSheet
const styles = StyleSheet.create({
  container: { marginTop: 10, padding: 5 }
});

<View style={styles.container} />
```

### ❌ Anti-Pattern 3: Async in useEffect Without isMounted
```typescript
// Crashes on unmount
useEffect(() => {
  fetchData().then(setData);
}, []);

// ✅ Use isMounted pattern (see Rule 4)
```

### ❌ Anti-Pattern 4: Missing Cleanup
```typescript
// Leaks subscription
useEffect(() => {
  const sub = subscribe(callback);
}, []);

// ✅ Always return cleanup
useEffect(() => {
  const sub = subscribe(callback);
  return () => sub.unsubscribe();
}, []);
```

### ❌ Anti-Pattern 5: Redundant Animation Triggers with Animated.Value

**Problem:** Clicking an already-selected button that triggers animation recreation causes native crashes in React Native's animation system.

**Symptom:** App crashes instantly when clicking an animated button that's already selected (no JavaScript logs, native crash).

**Root Cause:** Animation system race condition when trying to animate from current state to same state.

**❌ Don't:**
```typescript
// Crashes when clicking "All" while already on "All"
<Pressable onPress={() => onSelectCategory(category.id)}>
  <Animated.View style={{ opacity: animatedValue }}>
    <Text>{category.name}</Text>
  </Animated.View>
</Pressable>
```

**✅ Do:**
```typescript
// Disable button when already selected to prevent redundant animation
const renderCategory = (category, index) => {
  const isSelected = selectedCategory === category.id;

  // CRITICAL: Disable redundant clicks that would trigger same animation
  const shouldDisable = isSelected && category.id === 'all';

  return (
    <Pressable
      disabled={shouldDisable}
      onPress={() => onSelectCategory(category.id)}
    >
      <Animated.View style={{ opacity: animatedValues[index].opacity }}>
        <Text>{category.name}</Text>
      </Animated.View>
    </Pressable>
  );
};
```

**Why This Works:**
1. `disabled={shouldDisable}` prevents press events from reaching the animation system
2. Selective disabling (only when `isSelected && category.id === 'all'`) allows useful re-clicks (e.g., to clear filters)
3. No stale closures - button knows current selection state

**Additional Fix: useCallback Dependencies**

If the handler needs to check current state, add proper dependencies:

```typescript
// ❌ Stale closure - doesn't see state updates
const handleSelect = useCallback((id) => {
  if (selectedId === null) { // Always sees initial value!
    resetFilters();
  }
}, []); // Empty deps = stale closure

// ✅ Fresh closure with dependencies
const handleSelect = useCallback((id) => {
  if (selectedId === null) { // Sees current value
    resetFilters();
  }
}, [selectedId, breadcrumbVisible]); // Dependencies allow state checks
```

**Related Files:**
- `src/components/[animated_menu].tsx` (renderCategory method)
- `src/components/[category_selector].tsx` (handleCategoryPress)
- `src/screens/[main_screen].tsx` (handleItemSelect with dependencies)

---

### ❌ Anti-Pattern 6: Metro Bundler Not Picking Up Code Changes

**Problem:** Modified code doesn't execute even after multiple Metro restarts and app reloads. The app continues running old cached code.

**Symptoms:**
- Console logs show old function names/messages despite code changes
- New functions you added never execute
- Modified logic doesn't reflect in app behavior
- Hot reload/fast refresh shows success but nothing changes

**Root Cause:** Metro's incremental bundler uses aggressive caching. When you modify deeply nested function logic (especially inside service methods), Metro sometimes fails to invalidate the cache even with:
- `r` (reload) in Expo terminal
- Shake device → Reload
- Killing and restarting Metro
- Clearing cache with `--clear`

**❌ Don't:**
```typescript
// Continuing to modify the same function and hoping Metro will pick it up
private async enrichKeychainsWithImages(items: DataItem[]): Promise<void> {
  console.log(`Processing ${items.length} items`); // Change #1 - not picked up

  // Add pattern enrichment logic
  for (const item of items) {
    await enrichmentService.enrichItem(item); // Change #2 - not picked up
  }

  console.log(`🎨 Pattern enrichment complete`); // Change #3 - still old code!
}
```

**✅ Do - Create a New Function:**
```typescript
// STEP 1: Create a completely NEW function with distinctive name
private async enrichAllPatternsForItems(items: DataItem[]): Promise<void> {
  // Use very distinctive logging (triple emoji makes it unmistakable)
  console.log(`🎨🎨🎨 [NEW enrichAllPatternsForItems] Processing ${items.length} items`);

  let enrichedCount = 0;
  for (const item of items) {
    const hasEnrichmentData = item.variant_id || item.variant_type;

    if (hasPatternData) {
      try {
        const enrichedItem = await enrichmentService.enrichItem(item);
        if (enrichedItem.enriched_data) {
          item.enriched_data = enrichedItem.enriched_data;
          enrichedCount++;
          console.log(`✅ [NEW] Enriched ${item.name}`);
        }
      } catch (error) {
        console.warn(`⚠️ [NEW] Failed to enrich:`, error);
      }
    }
  }

  console.log(`🎨🎨🎨 [NEW] Completed: ${enrichedCount}/${items.length} enriched`);
}

// STEP 2: Call the new function directly in main flow
async fetchItems() {
  const items = await this.enrichItemsWithImages(rawItems);

  // NEW: Direct call to new function (not buried in existing function)
  await this.enrichAllDataForItems(items);

  return items;
}

// STEP 3: Bump cache version to force fresh data
private generateCacheKey(prefix: string): string {
  // v12 → v13 (increment to invalidate all caches)
  const parts = ['v13', prefix]; // Changed version number
  // ...
}
```

**Why This Works:**

1. **New function name** - Metro sees it as a brand new addition to the module, forcing a rebuild of that section
2. **Distinctive logging** - Triple emojis (🎨🎨🎨) and `[NEW]` prefix make it impossible to miss in logs whether new code is running
3. **Direct call in main flow** - Not buried inside another function, making the call graph change more obvious to Metro
4. **Cache version bump** - Ensures no stale cached data from previous enrichment logic
5. **Separation of concerns** - Splitting pattern enrichment from keychain enrichment makes code clearer and helps Metro track dependencies

**Debugging Steps:**

When you suspect Metro isn't picking up changes:

```bash
# 1. Check logs for distinctive markers
tail -100 /path/to/log.txt | grep "🎨🎨🎨"

# 2. If old logs appear, create new function with NEW name
# 3. Add distinctive logging (triple emoji + [NEW] prefix)
# 4. Bump cache version number in cacheKey generation
# 5. Reload app (r in terminal or shake → Reload)
# 6. Verify distinctive logs appear
```

**When to Use This Pattern:**

- ✅ After 2+ reload attempts show old code still running
- ✅ When modifying deeply nested service methods
- ✅ When changes are inside existing functions (vs new files)
- ✅ When Metro restart + `--clear` doesn't help
- ❌ Not needed for new files (Metro always picks up new files)
- ❌ Not needed for top-level component changes (usually cached correctly)

**Alternative Approaches (try these first):**

```bash
# Less nuclear options to try before creating new functions:

# 1. Clear Metro cache and restart
npx expo start --clear

# 2. Clear watchman cache
watchman watch-del-all && npx expo start

# 3. Clear all caches (nuclear option)
rm -rf node_modules/.cache
rm -rf .expo
npx expo start --clear
```

**Related Pattern - Separation of Concerns:**

This anti-pattern reveals a deeper issue: functions doing too many things. When you have to create a new function to "escape" Metro caching, it's often a sign the original function was:
- Mixing multiple responsibilities (keychains + patterns)
- Too deeply nested in the call stack
- Difficult to test/debug independently

**Example Refactor:**
```typescript
// BEFORE: One function doing two things
private async enrichKeychainsWithImages(items) {
  // Keychain image loading
  // Pattern enrichment (hidden in same function)
}

// AFTER: Separated responsibilities (better for Metro AND code clarity)
private async enrichKeychainsWithImages(items) {
  // Only keychain logic
}

private async enrichAllPatternsForItems(items) {
  // Only pattern enrichment logic
}

// Explicit sequential calls in main flow
await this.enrichKeychainsWithImages(items);
await this.enrichAllPatternsForItems(items);
```

**Related Files:**
- `src/services/[data_service].ts` (data enrichment implementation)
- `src/services/[enrichment_service].ts` (enrichment logic)

**References:**
- Metro bundler issue tracker: Known cache invalidation bugs
- React Native Fast Refresh limitations: https://reactnative.dev/docs/fast-refresh#limitations

---

### ❌ Anti-Pattern 7: Setting Cookie Headers Directly in fetch()

**Problem:** React Native's `fetch()` on iOS (NSURLSession) and Android (OkHttp) **silently ignores** manually set `Cookie` headers. The request goes out with **no cookies**, resulting in 401 Unauthorized errors.

**Real-World Impact (2026-01-06):** Third-party API requests worked perfectly from curl but failed with 401 from React Native - even with identical cookies and headers. The issue took hours to diagnose because fetch silently ignores the Cookie header.

**❌ Don't - Cookie Header is Silently Ignored:**
```typescript
// This looks correct but DOES NOT WORK!
const response = await fetch('https://api.example.com/endpoint', {
  headers: {
    'Cookie': 'sessionid=abc123; authToken=xyz789', // Silently ignored!
    'Content-Type': 'application/json',
  },
});
// Request goes out with NO cookies - 401 Unauthorized
```

**✅ Do - Use Native Cookie Store:**
```typescript
import CookieManager from '@react-native-cookies/cookies';

// Step 1: Set cookies in native store (BEFORE fetch)
await CookieManager.set('https://api.example.com', {
  name: 'sessionid',
  value: 'abc123',
  domain: 'api.example.com',
  path: '/',
  expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  secure: true,
  httpOnly: false,
});

await CookieManager.set('https://api.example.com', {
  name: 'authToken',
  value: 'xyz789',
  domain: 'api.example.com',
  path: '/',
  expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  secure: true,
  httpOnly: false,
});

// Step 2: Fetch with credentials: 'include' (uses native cookie store)
const response = await fetch('https://api.example.com/endpoint', {
  credentials: 'include', // CRITICAL - tells fetch to use native cookies
  headers: {
    // NO Cookie header needed!
    'Content-Type': 'application/json',
  },
});
// Cookies are automatically attached from native store
```

**Why This Happens:**
- iOS uses `NSURLSession` which manages cookies via `NSHTTPCookieStorage`
- Android uses `OkHttp` which manages cookies via `CookieJar`
- React Native's `fetch` polyfill bridges to native networking, which ignores manual Cookie headers for security
- `credentials: 'include'` tells the native layer to attach cookies from its store

**Debugging Tips:**
```typescript
// Verify cookies were set correctly
const cookies = await CookieManager.get('https://api.example.com');
console.log('Cookies in native store:', Object.keys(cookies));

// Check for critical cookies
if (!cookies.sessionid || !cookies.authToken) {
  console.error('Missing critical cookies!');
}
```

**Helper Function Pattern:**
```typescript
async function setNativeCookies(url: string, cookieString: string): Promise<void> {
  const domain = new URL(url).hostname;
  const cookiePairs = cookieString.split('; ');

  for (const pair of cookiePairs) {
    const [name, ...valueParts] = pair.split('=');
    const value = valueParts.join('=');

    if (!name || !value) continue;

    await CookieManager.set(url, {
      name,
      value,
      domain,
      path: '/',
      expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      secure: true,
      httpOnly: false,
    });
  }
}

// Usage
await setNativeCookies('https://api.example.com', 'sessionid=abc123; authToken=xyz789');
const response = await fetch(url, { credentials: 'include' });
```

**Related Files:**
- `src/services/[api_service].ts` - `setNativeCookies()` implementation
- Your integration-specific SOPs for full implementation details

**References:**
- [@react-native-cookies/cookies](https://github.com/react-native-cookies/cookies)
- [React Native fetch credentials documentation](https://reactnative.dev/docs/network#using-fetch)

---

## Quick Reference

### Checklist for New Features
- [ ] Use objects instead of Map/Set for lookups
- [ ] Add isMounted to async useEffect hooks
- [ ] Minimize useEffect dependencies
- [ ] Return cleanup function from all useEffects
- [ ] Use disk-first image caching
- [ ] Memoize FlatList render items
- [ ] Extract styles to StyleSheet
- [ ] Use useCallback for event handlers
- [ ] Add render count debugging in development
- [ ] Disable already-selected animated buttons to prevent crashes
- [ ] Add distinctive logging when modifying existing service methods
- [ ] Use native cookie store (CookieManager) for cookie-authenticated requests

### Performance Red Flags
- 🚩 Map or Set in data processing path
- 🚩 useEffect with >2 dependencies
- 🚩 No cleanup function in useEffect with subscriptions
- 🚩 Inline styles or functions in render
- 🚩 FlatList without keyExtractor
- 🚩 Image without cachePolicy
- 🚩 setState in render (infinite loop)
- 🚩 Missing isMounted in async callbacks
- 🚩 Animated.View without disabled prop on redundant clicks
- 🚩 Code changes not appearing after multiple reloads (Metro cache issue)
- 🚩 `headers: { 'Cookie': ... }` in fetch (silently ignored in RN!)

---

## Related Files
- `src/services/[data_service].ts` - Data fetching patterns
- `src/hooks/[data_hook].ts` - Subscription patterns
- `src/components/common/[image_component].tsx` - Image caching
- `src/services/[memory_service].ts` - Memory management

## References
- React Native Performance: https://reactnative.dev/docs/performance
- expo-image caching: https://docs.expo.dev/versions/latest/sdk/image/
- Memory leak investigation: Task 2025-10-14

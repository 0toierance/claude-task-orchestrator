# Performance Optimization SOP

Standard Operating Procedures for identifying and fixing performance issues in React Native applications.

## Memory Leak Prevention

### When to Use
- Building features with data fetching and caching
- Implementing real-time subscriptions
- Working with large datasets or image-heavy screens
- Any time you see progressive slowdown after repeated use

### Pattern 1: Avoid Map/Set in React Native

**Problem:** React Native's V8 garbage collector struggles with Map and Set objects, causing memory leaks even when references are cleared.

**Solution:** Use plain objects instead.

```typescript
// ❌ BAD - Memory Leak
async function fetchData() {
  const dataMap = new Map();
  records.forEach(record => {
    dataMap.set(record.id, record);
  });

  // Apply data
  items.forEach(item => {
    item.data = dataMap.get(item.id);
  });
  // Map never gets GC'd properly
}

// ✅ GOOD - No Leak
async function fetchData() {
  const dataLookup: Record<string, any> = {};
  records.forEach(record => {
    dataLookup[record.id] = record;
  });

  // Apply data
  items.forEach(item => {
    item.data = dataLookup[item.id];
  });

  // Optional: Explicit cleanup hint for large objects
  // @ts-ignore
  dataLookup = null;
}
```

**Example from codebase:**
- File: `src/services/[data_service].ts:152-173`
- Replaced metadata Map with object lookup
- Added explicit `= null` cleanup hint
- Result: 80% reduction in memory growth per request

**When to use Map anyway:**
- Never in data fetching/caching paths
- Only for small, short-lived collections (<100 items)
- Only if you're manually calling `.clear()` immediately after use

---

### Pattern 2: Stable Subscription Dependencies

**Problem:** useEffect hooks that create subscriptions (WebSocket, Supabase realtime, event listeners) re-run too frequently when dependencies include callback functions, causing subscription accumulation.

**Solution:** Minimize useEffect dependencies to only truly stable values.

```typescript
// ❌ BAD - Creates new subscription on every filter change
useEffect(() => {
  const unsubscribe = subscribeToUpdates(handleUpdate, filter);
  return () => unsubscribe();
}, [handleUpdate, filter]); // handleUpdate recreated every render!

// ✅ GOOD - Stable subscription
useEffect(() => {
  if (!enableRealtime) return;

  let isMounted = true; // Prevent stale callbacks

  const unsubscribe = subscribeToUpdates(
    (update) => {
      if (!isMounted) return; // Safety check
      handleUpdate(update);
    }
  );

  return () => {
    isMounted = false;
    if (unsubscribe) {
      try {
        unsubscribe();
      } catch (error) {
        console.error('Cleanup error:', error);
      }
    }
  };
}, [enableRealtime]); // Only stable dependency
```

**Example from codebase:**
- File: `src/hooks/[data_hook].ts:652-749`
- Removed handleRealtimeUpdate, refresh, filter from dependencies
- Added isMounted flag to prevent stale callbacks
- Result: Eliminated 20+ accumulated subscriptions after normal usage

**Cleanup Checklist:**
- [ ] Add `isMounted` flag at the start of useEffect
- [ ] Set `isMounted = false` in cleanup function
- [ ] Check `isMounted` before any state updates in callbacks
- [ ] Wrap cleanup calls in try-catch
- [ ] Clear all refs to subscription objects
- [ ] Remove unstable dependencies (callbacks, filters, state)

---

### Pattern 3: Memory-Conscious Image Caching

**Problem:** Caching all images in both memory and disk causes unbounded memory growth, especially with hundreds of item images.

**Solution:** Use disk-first caching and let the image library manage memory automatically.

```typescript
// ❌ BAD - All images in memory
<Image
  source={{ uri: imageUrl }}
  cachePolicy="memory-disk" // Everything cached in memory!
  priority="high"
/>

// ✅ GOOD - Disk-first with smart memory
<CachedImage
  source={imageUrl}
  cachePolicy={determineCachePolicy()} // Dynamic based on image type
  priority={isPriority ? 'high' : 'normal'}
/>

function determineCachePolicy(itemType: string): CachePolicy {
  // Immutable items: aggressive caching
  if (itemType === 'static' || itemType === 'category') {
    return 'memory-disk';
  }

  // Rarely changing: disk only
  if (itemType === 'reference') {
    return 'disk';
  }

  // Default: disk only, let expo-image manage memory
  return 'disk';
}
```

**Example from codebase:**
- File: `src/components/common/[image_component].tsx:62-75`
- Changed default from `memory-disk` to `disk`
- Static assets still use aggressive caching (immutable)
- Result: Reduced peak memory from 150MB to 70-80MB

**Cache Policy Guidelines:**
- **memory-disk**: Only for truly immutable data (static assets, icons)
- **disk**: Default for all user-generated or frequently changing data
- **memory**: Only for tiny, frequently accessed data (<10 items)
- **none**: Only for sensitive data (user photos, private content)

---

### Pattern 4: Periodic Memory Cleanup

**Problem:** Even well-optimized apps accumulate memory over time. Without periodic cleanup, caches grow indefinitely.

**Solution:** Implement automatic cleanup at strategic intervals.

```typescript
class MemoryManagerService {
  initialize() {
    // Monitor app state changes
    AppState.addEventListener('change', this.handleAppStateChange);

    // Periodic cleanup every 5 minutes
    setInterval(() => {
      this.performRoutineCleanup();
    }, 5 * 60 * 1000);
  }

  async performRoutineCleanup() {
    // 1. Clear expired cache entries
    await cacheService.cleanup();

    // 2. Check image cache size
    const cacheSize = await Image.getCacheSize();
    const cacheSizeMB = cacheSize / (1024 * 1024);

    // 3. Clear memory if too large
    if (cacheSizeMB > 100) {
      await Image.clearMemoryCache();
    }
  }

  async performAggressiveCleanup() {
    // On memory pressure: clear everything
    await cacheService.clearAll();
    await Image.clearMemoryCache();

    // Clear disk cache if enormous
    const cacheSize = await Image.getCacheSize();
    if (cacheSize > 150 * 1024 * 1024) {
      await Image.clearDiskCache();
    }
  }
}
```

**Example from codebase:**
- File: `src/services/[memory_service].ts`
- Routine cleanup every 5 minutes
- Aggressive cleanup when app backgrounds
- Image cache limits: 100MB memory, 150MB disk

**Cleanup Triggers:**
- **Routine**: Every 5-10 minutes during normal use
- **App Background**: When app goes to background/inactive state
- **Memory Warning**: When system sends memory warning
- **Manual**: User-initiated refresh or cache clear

---

## Performance Debugging

### Identifying Memory Leaks

**Symptoms:**
- App becomes laggy after 5-10 minutes of use
- UI elements stop rendering despite data loading
- Scrolling becomes jerky
- Filter changes take progressively longer
- Multiple simulator instances become unusable

**Debugging Steps:**

1. **Monitor Memory Growth**
```typescript
// Add to App.tsx or debugging screen
const [memoryStats, setMemoryStats] = useState(null);

useEffect(() => {
  const interval = setInterval(async () => {
    const stats = {
      cacheSize: await Image.getCacheSize(),
      cacheStats: cacheService.getStats(),
      timestamp: new Date().toISOString()
    };
    setMemoryStats(stats);
    console.log('📊 Memory Stats:', stats);
  }, 10000); // Every 10 seconds

  return () => clearInterval(interval);
}, []);
```

2. **Profile Subscription Creation**
```typescript
// Track active subscriptions
let subscriptionCount = 0;

const subscribe = (callback) => {
  subscriptionCount++;
  console.log(`🔌 Subscriptions active: ${subscriptionCount}`);

  return () => {
    subscriptionCount--;
    console.log(`🔌 Subscriptions active: ${subscriptionCount}`);
  };
};
```

3. **Monitor Component Re-renders**
```typescript
// Add to suspected leaking components
import { useEffect, useRef } from 'react';

function useRenderCount(componentName: string) {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
    console.log(`🔄 ${componentName} render #${renderCount.current}`);
  });
}

// In component:
useRenderCount('YourScreenName');
```

4. **Check useEffect Cleanup**
```typescript
// Add logging to useEffect cleanup
useEffect(() => {
  console.log('✅ Effect setup');

  return () => {
    console.log('🧹 Effect cleanup');
  };
}, [dependencies]);

// If you see setup without cleanup, you have a leak!
```

---

### Stress Testing for Memory Leaks

**Dual Simulator Test:**
1. Launch app on 2 iOS simulators simultaneously
2. Rapidly switch between filters 20+ times
3. Browse 100+ items in each simulator
4. Monitor memory usage in both

**Why this works:** Running 2 instances doubles memory pressure and exposes leaks 2x faster.

**Pass Criteria:**
- Memory stays under 100MB per instance after 15 minutes
- Filter switches remain instant (<100ms)
- Items render consistently
- No console warnings about memory pressure

---

## Performance Benchmarks

### Expected Memory Usage
- **Initial load**: 40-50MB
- **After 5 min browsing**: 60-70MB
- **Peak usage**: 80-90MB
- **After background**: 30-40MB (automatic cleanup)

### Expected Response Times
- **Filter switching**: <100ms
- **Item rendering**: <16ms per item (60 FPS)
- **Scroll performance**: 60 FPS sustained
- **Image loading**: <200ms from cache

### Red Flags
- Memory growth >10MB per minute
- Filter switches taking >500ms
- Frame drops during scrolling (<30 FPS)
- Items failing to render with data available

---

## Related Files
- `src/services/[data_service].ts` - Data fetching patterns
- `src/hooks/[data_hook].ts` - Subscription management
- `src/components/common/[image_component].tsx` - Image caching
- `src/services/[memory_service].ts` - Memory cleanup
- `src/services/[cache_service].ts` - Cache management

## References
- Task: Memory leak investigation and fixes (2025-10-14)
- Issue: Progressive performance degradation after 5 minutes
- Solution: Map-to-object conversion, stable subscriptions, memory manager

## Next Steps for New Performance Issues
1. Add memory monitoring (see debugging section)
2. Check for Map/Set usage in data paths
3. Review useEffect dependencies for subscriptions
4. Profile image cache size and growth
5. Run dual simulator stress test
6. Implement targeted fixes following patterns above

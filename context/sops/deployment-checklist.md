# Deployment Checklist SOP

## Related Documentation
- `security-protocols.md` - Pre-deployment security verification
- `api-design-standards.md` - API testing procedures
- `../system/dependencies.md` - Dependency versions and compatibility

---

## Overview

This SOP provides a comprehensive checklist for deploying application updates via Expo Application Services (EAS) Build.

**Deployment Workflow:**
1. **Development** → Local testing with `npm start`
2. **Preview** → Internal testing with EAS Preview build
3. **Production** → App Store submission with EAS Production build

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All TypeScript compilation errors resolved (`npx tsc --noEmit`)
- [ ] No console errors in development mode
- [ ] Git working directory clean (or intentional uncommitted changes)
- [ ] All new features behind feature flags (if applicable)
- [ ] No hardcoded API keys or secrets in code
- [ ] Environment variables properly configured in `app.json`

---

### Testing

**Local Testing:**
- [ ] iOS Simulator tested (`npm run ios`)
- [ ] Android Emulator tested (if applicable)
- [ ] All critical user flows tested manually:
  - [ ] OAuth login
  - [ ] Catalog browse
  - [ ] Item purchase flow
  - [ ] Order creation
  - [ ] Payment deposit
  - [ ] Identity verification (if changed)
  - [ ] Profile settings

**Data Integrity:**
- [ ] Database migrations tested in development
- [ ] Cache invalidation working correctly
- [ ] Real-time subscriptions functioning
- [ ] Image loading working (CachedImage component)

**Performance:**
- [ ] App launch time < 3 seconds
- [ ] Catalog loads within 2 seconds (cached)
- [ ] No memory leaks in long-running sessions
- [ ] Smooth scrolling in FlatLists

---

### Security

From `security-protocols.md`:
- [ ] All API keys stored in environment variables (never hardcoded)
- [ ] RLS policies enabled on user-specific tables
- [ ] Session cookies encrypted with device-specific + server keys
- [ ] Payment processing via backend API only
- [ ] Session tokens short-lived (24 hours)
- [ ] Profile structure validation before verification operations
- [ ] Audit logging enabled for security events
- [ ] Rate limiting configured (client + server)
- [ ] Transaction rollback detection active
- [ ] Session freshness protection (2-minute window)

---

### Dependencies

- [ ] All npm dependencies up to date (`npm outdated`)
- [ ] No critical security vulnerabilities (`npm audit`)
- [ ] Expo SDK version compatible with all libraries
- [ ] Supabase client version matches backend API
- [ ] React Native version stable (currently 0.81.4)

---

## EAS Build Configuration

### Build Profiles

Located in `eas.json`:

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": false
      }
    },
    "production": {
      "distribution": "store",
      "autoIncrement": true
    }
  }
}
```

---

### Environment Configuration

**app.json environment variables:**

```json
{
  "expo": {
    "extra": {
      "EXPO_PUBLIC_SUPABASE_URL": "https://[your_project_id].supabase.co",
      "EXPO_PUBLIC_SUPABASE_KEY": "eyJhbGci...",
      "API_KEY": "...",
      "VERIFICATION_API_URL": "https://[your-domain]/api/v1"
    }
  }
}
```

**Pre-deployment verification:**
- [ ] Supabase URL points to production project
- [ ] Supabase anon key is correct (not service role key!)
- [ ] External API keys valid
- [ ] Verification API URL updated (production URL, not ngrok)
- [ ] Stripe publishable key for production

---

## Build Process

### Development Build

**Purpose:** Local testing with dev client

```bash
# Build for iOS Simulator
eas build --platform ios --profile development

# After build completes:
# 1. Download .app file
# 2. Drag to Simulator
# 3. Test features
```

**When to use:**
- Testing new features locally
- Debugging complex issues
- Performance profiling

---

### Preview Build

**Purpose:** Internal testing on physical devices

```bash
# Build for internal distribution
eas build --platform all --profile preview

# After build completes:
# 1. Download IPA (iOS) / APK (Android)
# 2. Install via TestFlight (iOS) or direct install (Android)
# 3. Share with internal testers
```

**Internal Testing Checklist:**
- [ ] Test on multiple devices (iPhone 12+, Android 10+)
- [ ] Test with production API endpoints
- [ ] Verify OAuth authentication works
- [ ] Test order creation end-to-end
- [ ] Verify payment flow (Stripe test mode)
- [ ] Check identity verification flow
- [ ] Monitor crash reports
- [ ] Gather tester feedback

---

### Production Build

**Purpose:** App Store submission

```bash
# Build for production release
eas build --platform all --profile production

# After build completes:
# 1. Download IPA (iOS) / AAB (Android)
# 2. Submit to App Store Connect / Google Play Console
# 3. Monitor submission status
```

**Pre-Production Verification:**
- [ ] All preview testing passed
- [ ] Critical bugs resolved
- [ ] Performance meets targets
- [ ] Security audit completed
- [ ] Legal compliance verified (GDPR, PCI DSS)
- [ ] App Store metadata ready (screenshots, description)
- [ ] Version number incremented
- [ ] Release notes written

---

## Post-Build Verification

### Smoke Testing

**After installing build:**
- [ ] App launches successfully
- [ ] No crash on startup
- [ ] Login flow works
- [ ] Main screens load correctly
- [ ] API connectivity working
- [ ] Images load properly

### Monitoring

**After production deployment:**
- [ ] Monitor error tracking (Sentry/Bugsnag if configured)
- [ ] Watch Supabase logs for errors
- [ ] Check server logs (Stripe, verification backend)
- [ ] Monitor user feedback
- [ ] Track key metrics:
  - Daily active users (DAU)
  - Order completion rate
  - Payment success rate
  - Verification success rate
  - App crash rate

---

## Rollback Procedure

**If critical issue found in production:**

1. **Immediate Actions:**
   ```bash
   # Revert to previous build
   eas submit --platform ios --latest
   # Or manually promote previous version in App Store Connect
   ```

2. **Communicate:**
   - Notify users via in-app message
   - Post update on status page
   - Alert internal team

3. **Fix and Re-Deploy:**
   - Identify root cause
   - Apply hotfix
   - Test thoroughly
   - Re-deploy with patch version

---

## Common Issues

### Build Failures

**Issue:** TypeScript errors during build
```bash
# Fix: Run local type check first
npx tsc --noEmit

# Resolve all errors, then retry build
```

**Issue:** Dependency conflicts
```bash
# Fix: Clear cache and reinstall
rm -rf node_modules
npm install

# Or use clean install
npm ci
```

**Issue:** Environment variable missing
```bash
# Fix: Verify app.json has all required variables
# Check EAS Secrets configuration
eas secret:list
```

---

### Runtime Issues

**Issue:** App crashes on launch
- Check Expo logs: `npx expo start`
- Review device logs (Xcode Organizer for iOS)
- Verify all native modules linked correctly

**Issue:** API calls failing
- Verify environment variables loaded correctly
- Check API endpoints are reachable
- Review network request logs
- Confirm authentication tokens valid

**Issue:** Images not loading
- Check CachedImage component usage
- Verify image URLs accessible
- Review cache configuration
- Check network connectivity

**Issue:** Webhook failures / JSON parse errors
- **Symptom:** `SyntaxError: JSON Parse error: Unexpected character: <`
- **Root cause:** HTML error pages (404/502) returned instead of JSON
- **Debug steps:**
  1. Check ngrok/proxy routing configuration FIRST (infrastructure layer)
  2. Verify backend server is running on correct port
  3. Test webhook endpoint directly: `curl https://your-domain.com/api/v1/webhook`
  4. Check ngrok inspector: `http://localhost:4040` for routing conflicts
  5. Review backend logs for actual errors
- **Common causes:**
  - Multiple services sharing single ngrok domain causing routing conflicts
  - Backend server not running on expected port
  - Proxy/load balancer misconfigured
  - Network firewall blocking webhook delivery
- **Solution:** Separate services to dedicated domains/ports
- **Reference:** [TASK-ID] - Webhook routing fix

---

## Version Management

### Versioning Strategy

**Semantic Versioning: MAJOR.MINOR.PATCH**

- **MAJOR** (1.x.x): Breaking changes, major feature releases
- **MINOR** (x.1.x): New features, backwards-compatible
- **PATCH** (x.x.1): Bug fixes, minor improvements

**Example:**
- `1.0.0` - Initial production release
- `1.1.0` - Added transaction processing
- `1.1.1` - Fixed transaction processing bug
- `1.2.0` - Added identity verification
- `2.0.0` - Complete UI redesign

---

### Build Numbers

**Auto-increment with EAS:**

```json
// eas.json
{
  "build": {
    "production": {
      "autoIncrement": true
    }
  }
}
```

This automatically increments iOS CFBundleVersion and Android versionCode.

---

## Submission Process

### iOS App Store

**App Store Connect:**
1. Log in to https://appstoreconnect.apple.com
2. Select your app
3. Create new version
4. Upload build via Transporter or EAS Submit
5. Fill metadata:
   - Version number
   - What's New
   - Screenshots (6.7", 6.5", 5.5")
   - App description
   - Keywords
   - Support URL
   - Privacy Policy URL
6. Submit for review
7. Monitor review status (typically 1-3 days)

**App Store Requirements:**
- [ ] Privacy Policy published
- [ ] Support email/website available
- [ ] App complies with App Store Review Guidelines
- [ ] Age rating set correctly (as appropriate for content)
- [ ] In-app purchases configured (if applicable)

---

### Google Play Store (Future)

**Google Play Console:**
1. Log in to https://play.google.com/console
2. Select app
3. Create new release
4. Upload AAB file
5. Fill metadata
6. Submit for review

---

## Quick Reference

### Build Commands

```bash
# Development
npm start                           # Start Expo dev server
npm run ios                         # Run on iOS Simulator
npm run android                     # Run on Android Emulator

# EAS Build
eas build --platform ios --profile development     # Dev client
eas build --platform ios --profile preview         # Internal testing
eas build --platform all --profile production      # Production release

# EAS Submit
eas submit --platform ios --latest                 # Submit latest build
eas submit --platform android --latest             # Submit to Play Store

# Utilities
npx tsc --noEmit                   # Type check
npm outdated                       # Check outdated packages
npm audit                          # Security audit
eas secret:list                    # List EAS secrets
```

---

### Environment URLs

**Development:**
- Supabase: `https://[your_project_id].supabase.co`
- Verification API: `http://localhost:8080/api/v1` (ngrok tunnel)
- Stripe Payments: `http://localhost:8080` (local server)

**Production:**
- Supabase: Same as development (single project) or separate production project
- Verification API: `https://production-api-url.com/api/v1`
- Stripe Payments: `https://production-payments-url.com`

---

## Related SOPs

- `security-protocols.md` - Security verification checklist
- `api-design-standards.md` - API testing procedures
- `database-optimization.md` - Database migration procedures

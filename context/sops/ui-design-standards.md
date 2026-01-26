# UI Design Standards

Standard operating procedures for UI/UX implementation in React Native applications.

## Table of Contents
- [Lottie Animation Integration](#lottie-animation-integration)
- [Component Styling Patterns](#component-styling-patterns)
- [Theme Usage](#theme-usage)

---

## Lottie Animation Integration

### When to Use
Use Lottie animations for:
- Loading states and empty states
- Onboarding flows and welcome screens
- Interactive feedback and micro-interactions
- Icon replacements where dynamic motion enhances UX

**Do not use** for:
- Heavy animations that impact performance
- Critical UI elements that must load instantly
- Areas requiring immediate interaction

### Package Selection

**Recommended:** `lottie-react-native`
- Direct React Native binding with better performance
- Smaller bundle size than expo-lottie
- Full control over animation props

**Avoid:** `expo-lottie`
- Wrapper around lottie-react-native (unnecessary abstraction)
- Adds complexity without benefits
- Use only if specifically required by Expo managed workflow

**Installation:**
```bash
npm install lottie-react-native@7.3.4
```

### Implementation Pattern

**1. Asset Placement:**
Place Lottie JSON files in `assets/animations/`:
```
assets/
  animations/
    dotted-spinner.json
    loading-hand.json
    success-check.json
```

**2. Import and Usage:**
```tsx
import LottieView from 'lottie-react-native';

<LottieView
  source={require('../assets/animations/animation-name.json')}
  autoPlay
  loop
  style={{ width: 120, height: 120 }}
/>
```

**3. Essential Props:**
- `source`: Use `require()` for bundled assets (relative path)
- `autoPlay`: Set to `true` for immediate playback
- `loop`: Set to `true` for continuous animations
- `style`: Always specify explicit `width` and `height` in pixels

**4. TypeScript Compatibility:**
Note: `lottie-react-native@7.3.4` type definitions do not include `accessibilityLabel` or `accessibilityRole` props.
- Wrap LottieView in a `<View>` with accessibility props if needed
- Container View provides semantic structure for screen readers

**Example:**
```tsx
<View style={styles.iconContainer}>
  <LottieView
    source={require('../../assets/animations/dotted-spinner.json')}
    autoPlay
    loop
    style={{ width: 120, height: 120 }}
  />
</View>
```

### Performance Considerations

**File Size:**
- **Target:** < 100KB per animation
- **Acceptable:** 100-500KB for welcome/onboarding screens
- **Avoid:** > 500KB (optimize using Lottie compression tools)

**Animation Complexity:**
- Keep frame count reasonable (72 frames @ 24fps = 3s is good baseline)
- Expect 60fps with native driver for simple animations
- Monitor GPU usage for complex animations with many layers

**Optimization Strategy:**
1. Start with unoptimized animation during development
2. Monitor bundle size and performance
3. Optimize only if issues arise (avoid premature optimization)
4. Use tools like `lottie-cli` or online compressors if needed

### Container Styling Best Practices

**Transparent Containers (Recommended):**
```tsx
// Minimal styling - lets animation be the focus
containerStyle: {
  backgroundColor: 'transparent',
  alignItems: 'center',
  justifyContent: 'center',
}
```

**Avoid Unnecessary Visual Noise:**
- Remove background colors that compete with animation
- Remove borders unless they serve a functional purpose
- Minimize padding to maximize animation prominence

**Before (cluttered):**
```tsx
{
  backgroundColor: theme.colors.surface.primary,  // Gray circle
  borderRadius: theme.borderRadius.full,
  padding: theme.spacing['8'],
  borderWidth: 1,
  borderColor: theme.colors.border.subtle,
}
```

**After (clean):**
```tsx
{
  backgroundColor: 'transparent',
  alignItems: 'center',
  justifyContent: 'center',
}
```

### Animation Sizing Strategy

**Approach:**
1. Start with icon-equivalent size (64x64px for Feather icons)
2. Scale up if animation has sufficient detail (120x120px is good for welcome screens)
3. Maintain square aspect ratio unless animation specifically designed otherwise
4. Consider screen size - larger animations for tablet/desktop

**Scaling Guidelines:**
- **Small (48-64px):** List items, buttons, inline feedback
- **Medium (96-120px):** Welcome screens, empty states, modal headers
- **Large (150-200px):** Full-screen onboarding, splash screens

### Common Pitfalls

**❌ Don't:**
- Use relative sizing (percentages) - causes inconsistent scaling
- Forget explicit `width` and `height` in `style` prop
- Use accessibility props directly on LottieView (TypeScript errors)
- Bundle multiple large animations without lazy loading

**✅ Do:**
- Use absolute pixel dimensions
- Wrap in View container for layout control
- Test on both iOS and Android
- Monitor app bundle size with multiple animations

### Checklist for Lottie Integration

- [ ] Animation file in `assets/animations/`
- [ ] Import LottieView from `lottie-react-native`
- [ ] `source` uses `require()` with relative path
- [ ] `autoPlay` and `loop` props configured
- [ ] Explicit `width` and `height` in `style`
- [ ] Container has transparent background (no visual noise)
- [ ] Tested on iOS simulator/device
- [ ] No TypeScript errors
- [ ] Animation maintains 60fps
- [ ] Bundle size impact acceptable

---

## Component Styling Patterns

(To be documented in future tasks)

---

## Theme Usage

(To be documented in future tasks)

---

**Files:**
- `src/screens/[profile_screen].tsx` (Lottie implementation example)
- `assets/animations/[animation_file].json`

**Reference:** Task [task_id]
**Added:** [date]

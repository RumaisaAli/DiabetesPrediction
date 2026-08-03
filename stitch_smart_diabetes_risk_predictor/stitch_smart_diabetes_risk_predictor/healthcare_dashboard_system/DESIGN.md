---
name: Healthcare Dashboard System
colors:
  surface: '#faf9f6'
  surface-dim: '#dbdad7'
  surface-bright: '#faf9f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f1'
  surface-container: '#efeeeb'
  surface-container-high: '#e9e8e5'
  surface-container-highest: '#e3e2e0'
  on-surface: '#1a1c1a'
  on-surface-variant: '#42474d'
  inverse-surface: '#2f312f'
  inverse-on-surface: '#f2f1ee'
  outline: '#72787e'
  outline-variant: '#c2c7ce'
  surface-tint: '#376282'
  primary: '#35607f'
  on-primary: '#ffffff'
  primary-container: '#4f7999'
  on-primary-container: '#fcfcff'
  inverse-primary: '#a1cbef'
  secondary: '#615e57'
  on-secondary: '#ffffff'
  secondary-container: '#e7e2d9'
  on-secondary-container: '#67645d'
  tertiary: '#715744'
  on-tertiary: '#ffffff'
  tertiary-container: '#8b6f5b'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cae6ff'
  primary-fixed-dim: '#a1cbef'
  on-primary-fixed: '#001e30'
  on-primary-fixed-variant: '#1c4b69'
  secondary-fixed: '#e7e2d9'
  secondary-fixed-dim: '#cbc6bd'
  on-secondary-fixed: '#1d1b16'
  on-secondary-fixed-variant: '#494640'
  tertiary-fixed: '#ffdcc4'
  tertiary-fixed-dim: '#e2c0a9'
  on-tertiary-fixed: '#2a1709'
  on-tertiary-fixed-variant: '#5a4230'
  background: '#faf9f6'
  on-background: '#1a1c1a'
  surface-variant: '#e3e2e0'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-tabular:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 24px
  gutter: 20px
  card-gap: 24px
  section-margin: 40px
---

## Brand & Style

This design system is anchored in a philosophy of **Modern Minimalist Care**. It prioritizes clarity, calm, and professional reliability to reduce cognitive load for healthcare providers. The aesthetic balances the clinical precision required for medical data with a warm, human-centric approach to interface design.

The style leverages **Soft Minimalism**, moving away from harsh "hospital whites" in favor of organic, warm tones. High-precision typography is paired with generous whitespace and "2xl" rounded corners to create an environment that feels approachable yet authoritative. The UI avoids unnecessary ornamentation, using depth and subtle tonal shifts rather than heavy borders to define structure.

## Colors

The palette is designed to evoke serenity and cleanliness without the sterile coldness of traditional medical software.

- **Backgrounds:** A warm white (`#FAF9F6`) serves as the canvas, reducing eye strain during long shifts.
- **Surfaces:** Soft beige (`#F5EFE6`) is used for card containers and navigation elements to provide a gentle contrast against the background.
- **Accents:** A muted blue (`#5D87A8`) functions as the primary action color, signifying trust and stability.
- **Highlights:** Light peach (`#FFDBC3`) and light orange (`#FFB38E`) are reserved for gentle warnings, highlights, and secondary data visualizations, providing warmth without triggering high-alert anxiety.
- **Status Tones:** Use highly desaturated versions of green and red for clinical status, maintaining the muted, professional atmosphere.

## Typography

This design system utilizes **Inter** for its exceptional legibility in data-heavy environments. The typographic hierarchy relies on weight and subtle color shifts (from Charcoal to Slate) rather than dramatic size changes.

For data tables and medical readings, always enable **tabular figures** to ensure numerical alignment. Use Medium (500) weights for primary labels to ensure they stand out against the soft beige surfaces. Avoid Thin or Light weights to maintain accessibility and readability under varied lighting conditions common in clinical settings.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** model. The sidebar remains fixed, while the main content area utilizes a fluid 12-column grid that maxes out at 1600px to prevent excessive line lengths.

- **Whitespace:** Emphasize generous internal padding within cards (minimum 24px) to give medical data "room to breathe."
- **Grid:** Use a 24px gutter for desktop layouts, scaling down to 16px for tablet and 12px for mobile.
- **Density:** Provide a "Comfortable" density by default, with a "Compact" toggle that reduces vertical padding in data tables by 40% for power users reviewing extensive patient histories.

## Elevation & Depth

Hierarchy is established through **Ambient Shadows** and **Tonal Layering** rather than high-contrast borders.

- **Level 0 (Background):** The base warm white surface.
- **Level 1 (Cards):** Soft beige surfaces with a very soft, diffused shadow: `0 4px 20px rgba(93, 135, 168, 0.04)`. Note the subtle blue tint in the shadow to maintain harmony with the accent color.
- **Level 2 (Modals/Popovers):** Higher elevation with a more pronounced shadow: `0 12px 40px rgba(0, 0, 0, 0.06)`.
- **Borders:** Use borders sparingly. When required, use a 1px solid line in a shade only 5% darker than the surface color to maintain the minimal aesthetic.

## Shapes

The design system adopts a **Large Rounded (2xl)** shape language. This "human" geometry softens the professional interface, making it feel modern and less institutional.

- **Main Cards:** 24px (1.5rem) corner radius.
- **Buttons & Inputs:** 12px (0.75rem) corner radius.
- **Badges & Chips:** Fully pill-shaped for maximum distinction from interactive buttons.
- **Selection States:** Use subtle rounded "ghost" backgrounds (8px radius) for navigation hover states.

## Components

### Cards
Cards are the primary structural unit. They should feature no visible border, using the soft beige surface and ambient shadow for definition. Card headers should be separated by a subtle 1px horizontal line or a simple 24px padding gap.

### Buttons
- **Primary:** Solid muted blue with white text. 
- **Secondary:** Warm white background with a thin soft beige border and muted blue text.
- **Tertiary:** Ghost style, using peach or orange highlights only for specific contextual actions (like "Flag" or "Urgent").

### Data Tables
Tables must be clean and borderless. Use zebra-striping with 2% opacity shifts or simple horizontal dividers in soft beige. Row hover states should utilize a subtle light-peach tint to indicate selection.

### Status Badges
Status badges use "Soft" styling: a low-opacity background of the status color (e.g., 10% opacity orange) with a high-contrast version of the same color for the text. This ensures the badge is legible without dominating the visual hierarchy.

### Input Fields
Inputs should have a soft beige background to blend with the card surfaces, moving to a warm white background with a 2px muted blue border on focus.
```markdown
# Design System Document: The Urban Monolith

## 1. Overview & Creative North Star
**Creative North Star: The Digital Architect**
This design system moves beyond the "app-as-a-utility" and treats the smart city interface as a living architectural extension. It is grounded in the precision of iOS native patterns but elevated through a high-end, editorial lens. We reject the "flatness" of typical dashboards in favor of **Tonal Depth** and **Intentional Asymmetry**. 

The goal is to provide a sense of civic calm. By utilizing a "Low-Saturation Emerald" palette and sophisticated Manrope/Inter typography pairings, we create an experience that feels like a premium concierge rather than a control panel. We prioritize the "Quiet UI"—where the information is the hero, and the interface is the elegant, invisible frame.

---

## 2. Colors & Surface Philosophy
The palette is rooted in deep obsidian tones and refined, botanical greens. It avoids the high-frequency "neon" vibrations of typical tech apps, opting instead for a matte, sophisticated finish.

### Core Tones
- **Primary (`#95d4ac`):** A desaturated emerald. Used for primary actions and brand moments.
- **Surface (`#131315`):** The standard iOS-inspired dark foundation.
- **Surface Tiers:** 
  - `surface_container_lowest` (#0e0e10) for background-level depth.
  - `surface_container_high` (#2a2a2c) for interactive card states.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. We define boundaries through **Tonal Shifting**. A card does not need a line to exist; it exists because its `surface_container_low` fill sits subtly against the `surface` background.

### The "Glass & Gradient" Rule
To elevate the "smart" nature of the city, use Glassmorphism for floating navigation bars or critical alerts. 
- Use a background color of `surface_container_high` at 70% opacity with a `20px` backdrop-blur. 
- For main CTAs, apply a subtle linear gradient from `primary` (#95d4ac) to `primary_container` (#609d78) at a 135-degree angle. This provides "soul" and a tactile, metallic quality.

---

## 3. Typography: The Editorial Edge
We employ a dual-font strategy to balance architectural authority with high-legibility data.

*   **Display & Headlines (Manrope):** Chosen for its geometric precision. Use `display-lg` to `headline-sm` for hero city data (e.g., "Air Quality Index") and section headers. The wider tracking in Manrope conveys a sense of expensive space.
*   **Body & Labels (Inter):** The workhorse. Inter provides the "Native iOS" feel users trust. Use `body-md` for general information and `label-sm` for metadata or technical city specs.

**Hierarchy Tip:** Never center-align long-form data. Use intentional left-aligned "ragged right" layouts to mimic high-end architectural journals.

---

## 4. Elevation & Depth
In this design system, depth is a functional tool, not a stylistic flourish.

### The Layering Principle
Stack tiers to create importance. 
- **Base:** `surface`
- **Sectioning:** `surface_container_low`
- **Actionable Card:** `surface_container_high`
This creates a "nested" look that feels like a physical architectural model.

### Ambient Shadows
Shadows must never be black. Use a tinted shadow based on `on_surface` (at 6% opacity) with a blur radius of `24px` and a `4px` Y-offset. This mimics natural ambient light hitting a matte surface.

### The "Ghost Border" Fallback
If high-density data requires a container, use a **Ghost Border**: 1px stroke using `outline_variant` (#404942) at 15% opacity. It should be felt, not seen.

---

## 5. Components

### Cards & Lists
*   **The Card:** Use `md` (0.75rem) or `lg` (1rem) corner radius. Never use dividers between list items. Instead, use a `12` (3rem) spacing gap or a 1-step shift in surface color to separate content blocks.
*   **Lists:** Leading elements (icons) should be housed in a `secondary_container` soft-square with 20% opacity to maintain the "muted" aesthetic.

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary_container`), `full` roundedness, and `on_primary` text.
*   **Secondary:** `surface_container_highest` fill with `primary` text. No border.
*   **Tertiary:** Ghost style. No background, `primary` text, high-weight typography.

### Input Fields
*   Background: `surface_container_low`.
*   Border: None, until focus. On focus, a `primary` Ghost Border (20% opacity).
*   Shape: `DEFAULT` (0.5rem) roundedness to contrast with the `full` roundedness of buttons.

### Smart City Specialized Components
*   **Status Orbs:** For city health (Traffic, Power), use a soft radial glow of the `primary` or `error` color, capped at 30% opacity, placed behind a semi-transparent `surface_container` icon.
*   **The "Glance" Chip:** Small, `label-md` text chips using `secondary_fixed_dim` backgrounds for quick-read data like "Live" or "Encrypted."

---

## 6. Do's and Don'ts

### Do
*   **Do** use `24` (6rem) or `20` (5rem) spacing for major section breathing room.
*   **Do** use "Optical Centering" for icons within emerald containers.
*   **Do** utilize `backdrop-filter: blur()` on any element that overlaps a map or data visualization.

### Don't
*   **Don't** use 100% opaque white for text. Use `on_surface` (#e4e2e4) for better optical comfort in dark mode.
*   **Don't** use "Electric" or "Neon" greens. If the green vibrates against the black, it is too saturated.
*   **Don't** use standard 1px lines to separate header from body. Use a `surface_container_low` block or simple white space.
*   **Don't** use "Drop Shadows" on cards sitting on the base background; use Tonal Layering instead. Only use shadows for "Floating" elements like Modals or Tooltips.
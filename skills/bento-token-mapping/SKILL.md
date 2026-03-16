---
name: bento-token-mapping
user-invocable: false
description: Verify current Bento token APIs from live source and map Figma spacing, radius, typography, stroke, and colors safely.
---

# Bento Token Mapping

Use this skill when translating Figma or design specs to Bento tokens, or when reviewing iOS UI code for token correctness.

## Source of truth

Never trust old tables or memory. Read current Bento token source from the checked out repo first.

Default token files in `pd-mob-ui-kit-ios`:
- `Bento/Sources/Theme/Tokens/Spacing.swift`
- `Bento/Sources/Theme/Tokens/CornerRadius.swift`
- `Bento/Sources/Theme/Tokens/Font.swift`
- `Bento/Sources/Theme/Tokens/Stroke.swift`
- `Bento/Sources/Theme/Tokens/Color/UIColor+Extension.generated.swift`
- `Bento/Sources/Theme/Tokens/Color/ColorTokens.generated.swift` for aliases, deprecations, and generated names

If a token name is not visible in those files, do not invent it.

## Current token families

### Spacing
Current `CGFloat` accessors are:
- `.spacingXxxs`, `.spacingXxs`, `.spacingXs`, `.spacingSt`, `.spacingSm`
- `.spacingMd`, `.spacingLg`, `.spacingXl`, `.spacingXxl`, `.spacingXxxl`

### Corner radius
Use semantic radius tokens, not just raw pt values. Current accessors include:
- `.cornerRadiusMini`
- `.cornerRadiusBase`
- `.cornerRadiusButton`
- `.cornerRadiusMedia`
- `.cornerRadiusContainer`
- `.cornerRadiusField`
- `.cornerRadiusContainerEdge`
- `.cornerRadiusOverlay`
- `.cornerRadiusPill`
- `.cornerRadiusCircle`
- pressed variants such as `.cornerRadiusBasePressed`, `.cornerRadiusButtonPressed`, `.cornerRadiusContainerPressed`, `.cornerRadiusFieldPressed`
- `.cornerRadiusSwitch`

### Typography
Current Bento typography is defined in `Font.swift`. Prefer the live API names:
- `UIFont.titleDp`, `titleLg`, `titleMd`, `titleMdStrong`, `titleSm`
- `UIFont.body`, `bodySm`, `bodyXs`
- `UIFont.highlight`, `highlightSm`, `highlightXs`
- matching SwiftUI `Font` accessors exist

Older `heading*`, `bodyLarge`, or `caption` tables are stale unless the current repo still exposes them.

### Stroke
Current stroke tokens are semantic, not numeric aliases:
- `.strokeDivider`
- `.strokeIcon`
- `.strokeInput`
- `.strokeInputFocus`
- `.strokeInteractive`
- `.strokeInteractiveFocus`
- `.strokeInteractiveHover`
- `.strokeInteractiveSubtle`
- `.strokeNavigation`
- `.strokeElevated`
- `.strokeSelection`
- `.strokeStatic`

Do not assume `.strokeWidth1`, `.strokeWidth2`, or `stroke/primary` style names exist unless the current source shows them.

### Colors
Color accessors and aliases are generated. Verify each one in generated extensions before using it.
Known current examples that exist in Bento:
- `.interactionPrimary`
- `.neutralPrimary`
- `.successHighlight`
- `.proDealHighlight1`

For color mapping, search the generated files with the exact Figma token, alias, or hex-related name before concluding there is no match.

## Mapping workflow

1. Read the relevant token source files first.
2. Map by semantic intent before raw numeric match.
3. If Figma gives a token name, search that exact string in the generated color/token files.
4. If Figma gives only a raw value, choose the closest current semantic token and mark the mapping as inferred.
5. When a token is deprecated, prefer the replacement shown in generated files and say that the old name is deprecated.
6. In answers, include the source file path that confirmed the token.

## Review rules

- Never use raw hex colors when a Bento token exists.
- Never use raw spacing in new UI code.
- Never hardcode font sizes when Bento typography covers the case.
- Never assume an 8pt radius means `.cornerRadiusBase`; pick the semantic token for the component type.
- Never rely on stale token names copied from older specs.
- Avoid `roundCorners(corners:radius:)` when `layer.cornerRadius` plus masked corners is enough.

### Asymmetric padding rule

If Figma specifies **different values for top and bottom** (or left and right) padding, always declare **two separate named constants** — never collapse them into one.

```swift
// CORRECT — top and bottom are different Bento tokens
private enum Layout {
  static let contentTopPadding = CGFloat.spacingMd    // 24pt
  static let buttonBottomPadding = CGFloat.spacingSm  // 16pt
}

// WRONG — merges two distinct spacings into one name, causing incorrect layout
private enum Layout {
  static let verticalPadding = CGFloat.spacingXs  // wrong for both edges
}
```

Treat any Figma spec where `paddingTop ≠ paddingBottom` (or `paddingLeft ≠ paddingRight`) as asymmetric and split accordingly.

## Helpful search patterns

- `rg -n "tokenName" Bento/Sources/Theme/Tokens/Color`
- `rg -n "static var .*title|body|highlight" Bento/Sources/Theme/Tokens/Font.swift`
- `rg -n "static var .*spacing|cornerRadius|stroke" Bento/Sources/Theme/Tokens`

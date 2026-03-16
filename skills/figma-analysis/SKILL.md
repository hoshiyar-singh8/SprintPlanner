---
name: figma-analysis
user-invocable: false
description: Figma URL parsing, get_design_context usage, design diffs
---

# Figma Analysis Skill

Background knowledge for agents that need to read Figma designs and produce structured design diffs.

## Figma URL Parsing

Extract `fileKey` and `nodeId` from Figma URLs:

| URL Format | fileKey | nodeId |
|------------|---------|--------|
| `figma.com/design/:fileKey/:fileName?node-id=:int1-:int2` | `:fileKey` | Convert `-` to `:` (e.g., `698-45462` → `698:45462`) |
| `figma.com/design/:fileKey/branch/:branchKey/:fileName` | Use `:branchKey` | Same conversion |
| `figma.com/board/:fileKey/:fileName` | `:fileKey` (FigJam) | Same conversion |

## get_design_context Usage

This is the primary tool for reading Figma designs:

```
get_design_context(nodeId: "698:45462", fileKey: "abc123def")
```

Returns:
- Reference code (React+Tailwind — treat as SPECIFICATION, not code)
- Screenshot of the design
- Contextual metadata (tokens, variables, component docs)

### When to call get_metadata first
- If the node is a page or large frame and you need to find specific sub-nodes
- If the structure is unclear from the URL alone
- Returns XML with node IDs, layer types, names, positions, sizes

## iOS Platform + Figma URL: Hard Stop

If platform is **iOS** and Figma URLs are provided:

> "Before reading Figma, run **`/ios-ui-spec`** on each component URL first.
> That specialist maps every token to Bento and generates UIStackView + `update(with:)` code.
> Paste the spec blocks here — I'll incorporate them directly.
> _(Say 'proceed without spec' to read Figma myself — tokens marked unverified.)_"

- **If user provides `/ios-ui-spec` blocks**: Use verbatim. Do NOT call `get_design_context`.
- **If user says 'proceed without spec'**: Read Figma directly, mark tokens as `⚠️ unverified`.

## Design Change Summary (Before/After Diff)

For each screen with before + after URLs, produce:

```markdown
**Screen: [Screen Name]**
| Aspect | Before (Current) | After (Target) |
|--------|------------------|----------------|
| Components added | — | [new components] |
| Components removed | [removed] | — |
| Components modified | [component] | [what changed] |
| Layout changes | [current] | [new] |
| New states | — | [loading, empty, error] |
| Copy changes | [old text] | [new text] |
```

Ask: "Is this diff correct? Anything I missed or misread?"

## Token Extraction from Figma Output

From `get_design_context` output, extract:
- Exact padding: top/bottom/left/right in pt
- Gap between elements in pt
- Corner radius values and which corners
- Icon name and size (e.g., `ic-voucher-filled`, 24x24pt)
- Font tokens → map to platform design system
- Color tokens → map to platform design system

## ASCII Layout Diagrams

Always render extracted layout as ASCII art:
```
[UIImageView 24×24] ──8pt── [UILabel flex] ──8pt── [UILabel CTA]
└──── 16pt ──────────────────────────────────────────── 16pt ────┘
                     8pt top / 8pt bottom
```

## Figma Output Interpretation Rules

1. **React/Tailwind code = specification, NOT implementation code**
   - Translate components and tokens to platform-native equivalents
   - Never copy Figma output verbatim into task descriptions
2. **`px` values from Figma = pt values on iOS**
3. **Hex colors must be mapped to design system tokens** (e.g., Bento for iOS)
4. **Tailwind classes indicate intent** (e.g., `rounded-lg` → corner radius token)
5. **Absolute-positioned elements are NOT layout anchors**
   - If a Figma layer has `position: absolute` (i.e. it is outside the auto-layout flow), it is a decorative overlay and must NOT be used as a UIKit anchor for sibling or child elements.
   - Common culprits: drag handles on bottom sheets, badge overlays, floating icons.
   - **Correct pattern:** anchor the next auto-layout element directly to the container's `topAnchor` (or `bottomAnchor`) with the appropriate spacing constant.

   ```swift
   // WRONG — dragHandle is absolute; chains layout through it
   contentStack.topAnchor.constraint(equalTo: dragHandle.bottomAnchor, constant: Layout.contentTopPadding)

   // CORRECT — anchor to the container, skip the absolute element
   contentStack.topAnchor.constraint(equalTo: topAnchor, constant: Layout.contentTopPadding)
   ```

   When writing UIKit code from a Figma spec, inspect whether each element you reference is in the auto-layout frame or is absolutely positioned before using it as an anchor.

## Ambiguity Resolution

If any change is unclear from Figma output, ask specifically:
- "I see [component X] changed but I'm not sure whether [specific ambiguity]."
- Common ambiguities: conditional visibility, animation/transitions, interactive states, responsive behavior, dark mode variants
- **Never guess about visual changes** — always ask

## Consolidated UI Change Summary

After processing all screens:
```markdown
Full UI scope:
- **[Screen 1]**: [1-line summary]
- **[Screen 2]**: [1-line summary]

Total: [N] screens, [M] new components, [K] modified components.
```

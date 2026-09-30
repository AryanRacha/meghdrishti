# 10 - Guided Tour Enter Control

## Objective
Configure Meghdrishti's Guided Tour (Story Mode) to require manual progression via the **Enter** key while preserving the visual progress timing line atop each step.

## Changes Made
1. **`frontend/src/hooks/useStoryMode.ts`**:
   - Kept step actions and `caption.durationMs` timing line.
   - Replaced automatic timeout progression with an `Enter` key / manual `next()` promise resolver.
   - Added `next()` handler to trigger advancement on `Enter` keydown or UI button click.
   - Added cancellation guard to stop in-flight step animations if `Enter` is pressed early.
2. **`frontend/src/components/panels/StoryBar.tsx`**:
   - Preserved `story-progress ${caption.durationMs}ms linear forwards` CSS progress animation.
   - Added a `Next ↵` button with keyboard shortcut badge alongside the existing `Esc` button.
3. **`frontend/src/App.tsx`**:
   - Passed `onNext={story.next}` to `StoryBar`.

## Keyboard Controls
- `Enter`: Advance to the next tour step.
- `Escape`: Stop and exit Guided Tour.

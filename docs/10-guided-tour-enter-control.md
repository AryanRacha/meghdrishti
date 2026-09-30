# 10 - Guided Tour Enter Control

## Objective
Configure Meghdrishti's Guided Tour (Story Mode) to require manual progression via the **Enter** key while preserving the visual progress timing line atop each step.

## Changes Made
1. **`frontend/src/hooks/useStoryMode.ts`**:
   - Replaced linear loop with a bidirectional state machine supporting forward (`next()`) and backward (`prev()`) navigation.
   - Handled keyboard bindings: `ArrowRight` or `Enter` for next, `ArrowLeft` for previous, `Escape` to stop.
   - Preserved timing line animation and in-flight cancellation guards.
2. **`frontend/src/components/panels/StoryBar.tsx`**:
   - Added a `‹ Back [←]` button (disabled on step 0).
   - Updated the `Next › [→]` button (shows `Finish` on the final step) with arrow key and Enter badges.
3. **`frontend/src/lib/storyScript.ts`**:
   - Made every step's `run()` function idempotent so navigating backward restores the exact required map view, layers, variables, and modals.
4. **`frontend/src/App.tsx`**:
   - Passed `onPrev={story.prev}` to `StoryBar`.

## Keyboard Controls
- `ArrowRight` or `Enter`: Advance to the next tour step (or finish).
- `ArrowLeft`: Return to the previous tour step.
- `Escape`: Stop and exit Guided Tour.

## Tour Sequence (20 Steps)
1. Context & Architecture (Introduction, Core Physics vs AI Dilemma, Super-UNet Residual Network, Extreme-Weighted Loss).
2. Physical NWP vs AI vs Blended Comparison (NOAA GFS, Data-driven AI, Super-UNet Blending, Interactive Swipe Compare).
3. Explainable AI (Trust Map, **XAI Pixel Inspector** sampling Mandi/Himachal cloudburst epicenter).
4. Meteorological Horizons (Variable switching, FiLM Lead-time conditioning from +24h to +120h, Monsoon Time-lapse).
5. Impact-Based Disaster Decision Support (Threat Matrix, Top Threat, GIS Population Exposure, Multi-lingual Regional TTS Audio Warning, Emergency Dispatch, **Official IMD/NDMA Civil Advisory Bulletin**).
6. Outro.

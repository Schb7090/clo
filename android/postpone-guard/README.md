# Postpone Guard (Android)

A small Android app with one feature. When a task has been postponed for three
or more days, it shows a full-screen, opaque overlay over other apps with the task
and two buttons, **DONE** and **SKIP TODAY**.

## Rules
| Rule | Where |
|---|---|
| Appears from the 3rd postponed day (`postponedDays >= 3`) | `core/.../Item.kt` `Items.overlayCandidate` |
| Shows the top item: most postponed, then oldest; not done; not skipped today | `Items.ORDER` |
| Only while the user is active: screen on and unlocked | `OverlayService.screenUsable` |
| Never during a call (ringing or active, telephony or VoIP audio mode) | `env/CallState.kt` |
| Never in front of the dialler, an emergency app or a navigation app | `core/.../BlockedPackages.kt` |
| Never during background navigation, if notification access is granted | `env/NavNotificationListener.kt` |
| Holding a finger anywhere for 5 s dismisses it | `core/.../HoldDetector.kt`, `overlay/OverlayView.kt` |
| Shows at most once per 30 minutes, counted from when it appeared | `OverlayPolicy.CAP_MILLIS` |
| Fails safe: if the app or the call state can't be read, it does not show | `OverlayPolicy.blocker` |

While the overlay is up, the service re-checks every second, and at once on a
call-state change. It removes the overlay if a call starts, or a blocked app or
navigation comes up.

DONE marks the task done. SKIP TODAY hides the task until tomorrow and counts as
today's postponement. The 5 s escape closes the overlay without changing the
task. Back is ignored.

## Permissions (granted on the main screen)
- Display over other apps (`SYSTEM_ALERT_WINDOW`)
- Usage access (`PACKAGE_USAGE_STATS`), to see which app is in front
- Phone state (`READ_PHONE_STATE`), and on Android 13+ notifications for the service notification
- Optional: notification access, to detect navigation running in the background

## Build
```bash
./gradlew :core:test          # pure-Kotlin rules, runs without the Android SDK
./gradlew :app:assembleDebug  # needs the Android SDK (platform 35)
```
Install `app/build/outputs/apk/debug/app-debug.apk`, open the app, grant the
permissions, add a task and press **Postpone** on three different days. To test
without waiting, use **Preview overlay**. It skips the day rule and the cap, but
not the call, app and navigation checks.

## Known limits
- **Package lists are best effort.** Dialler, emergency and navigation apps
  differ by OEM, and the names in `BlockedPackages.kt` are not all verified on
  devices. The system default dialler is always detected.
- **Background navigation** (for example Maps guiding while another app is open)
  is detected only through the optional notification access. Without it, only a
  navigation app in front blocks the overlay.
- Since Android 8, app overlays (`TYPE_APPLICATION_OVERLAY`) sit below the
  status bar and the system navigation, so Home and the notification shade still
  work. Leaving that way also counts toward the 30-minute cap.
- Tested in this repository by unit tests and a debug build with lint only. It has
  not been run on a device or an emulator.

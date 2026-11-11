package app.postponeguard.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

class OverlayPolicyTest {
    private val today = LocalDate.of(2026, 11, 11)
    private val now = 1_000_000_000L
    private val min = 60_000L

    private fun item(days: Int, id: String = "a", created: Long = 0, skipped: LocalDate? = null, done: Boolean = false) =
        Item(id, "Task $id", created, postponedDays = days, skippedOn = skipped, done = done)

    private fun env(
        lastShown: Long? = null,
        active: Boolean = true,
        inCall: Boolean? = false,
        fg: String? = "com.example.notes",
        dialer: String? = null,
        bgNav: Boolean = false,
    ) = Environment(today, now, lastShown, active, inCall, fg, dialer, bgNav)

    private fun reason(items: List<Item>, e: Environment) = (OverlayPolicy.decide(items, e) as Decision.Hide).reason

    @Test fun day2Hidden_day3Shown() {
        assertEquals(Reason.NO_ITEM, reason(listOf(item(2)), env()))
        assertTrue(OverlayPolicy.decide(listOf(item(3)), env()) is Decision.Show)
    }

    @Test fun showsTopItem() {
        val items = listOf(item(3, "old", created = 1), item(5, "most", created = 9), item(5, "older", created = 2))
        assertEquals("older", (OverlayPolicy.decide(items, env()) as Decision.Show).item.id)
    }

    @Test fun doneAndSkippedItemsIgnored() {
        assertEquals(Reason.NO_ITEM, reason(listOf(item(4, done = true)), env()))
        assertEquals(Reason.NO_ITEM, reason(listOf(item(4, skipped = today)), env()))
        assertTrue(OverlayPolicy.decide(listOf(item(4, skipped = today.minusDays(1))), env()) is Decision.Show)
    }

    @Test fun inactiveOrLockedHidden() {
        assertEquals(Reason.USER_INACTIVE, reason(listOf(item(3)), env(active = false)))
    }

    @Test fun callsHidden() {
        assertEquals(Reason.IN_CALL, reason(listOf(item(3)), env(inCall = true)))
        assertEquals(Reason.CALL_STATE_UNKNOWN, reason(listOf(item(3)), env(inCall = null)))
    }

    @Test fun blockedForegroundApps() {
        assertEquals(Reason.DIALLER, reason(listOf(item(3)), env(fg = "com.google.android.dialer")))
        assertEquals(Reason.DIALLER, reason(listOf(item(3)), env(fg = "com.oem.phone", dialer = "com.oem.phone")))
        assertEquals(Reason.EMERGENCY, reason(listOf(item(3)), env(fg = "com.android.emergency")))
        assertEquals(Reason.NAVIGATION, reason(listOf(item(3)), env(fg = "com.waze")))
        assertEquals(Reason.NAVIGATION, reason(listOf(item(3)), env(bgNav = true)))
        assertEquals(Reason.FOREGROUND_UNKNOWN, reason(listOf(item(3)), env(fg = null)))
    }

    @Test fun thirtyMinuteCap() {
        assertEquals(Reason.CAPPED, reason(listOf(item(3)), env(lastShown = now - 29 * min)))
        assertTrue(OverlayPolicy.decide(listOf(item(3)), env(lastShown = now - 30 * min)) is Decision.Show)
    }

    @Test fun blockerIgnoresCap() {
        assertEquals(null, OverlayPolicy.blocker(env(lastShown = now)))
        assertEquals(Reason.IN_CALL, OverlayPolicy.blocker(env(inCall = true)))
    }

    @Test fun postponeOncePerDay_skipCountsAsPostpone() {
        val a = Items.postpone(item(0), today)
        assertEquals(1, a.postponedDays)
        assertEquals(1, Items.postpone(a, today).postponedDays)
        assertEquals(2, Items.postpone(a, today.plusDays(1)).postponedDays)
        val s = Items.skipToday(item(3), today)
        assertEquals(4, s.postponedDays)
        assertEquals(today, s.skippedOn)
        assertFalse(Items.skipToday(a, today).postponedDays > 1)
    }
}

class HoldDetectorTest {
    @Test fun firesOnceAfterFiveSeconds() {
        val h = HoldDetector(5_000, slopPx = 10f)
        h.down(0, 100f, 100f)
        assertFalse(h.tick(4_999))
        assertEquals(0.5f, h.progress(2_500), 0.001f)
        assertTrue(h.tick(5_000))
        assertFalse(h.tick(6_000))
    }

    @Test fun releaseOrMoveCancels() {
        val h = HoldDetector(5_000, slopPx = 10f)
        h.down(0, 0f, 0f); h.cancel()
        assertFalse(h.tick(5_000))
        h.down(0, 0f, 0f); h.move(5f, 5f)
        assertTrue(h.isHolding)
        h.move(20f, 0f)
        assertFalse(h.tick(5_000))
    }
}

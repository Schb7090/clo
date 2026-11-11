package app.postponeguard.env

import android.app.Notification
import android.os.Build
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import app.postponeguard.core.BlockedPackages

/**
 * Optional. When the user grants notification access, this detects navigation
 * running in the background (an ongoing notification from a navigation app, or
 * one with the navigation category). Without it, only a navigation app in the
 * foreground blocks the overlay.
 */
class NavNotificationListener : NotificationListenerService() {
    override fun onListenerConnected() = refresh()
    override fun onListenerDisconnected() { navigating = false }
    override fun onNotificationPosted(sbn: StatusBarNotification) = refresh()
    override fun onNotificationRemoved(sbn: StatusBarNotification) = refresh()

    private fun refresh() {
        navigating = try {
            activeNotifications.orEmpty().any(::isNavigation)
        } catch (e: SecurityException) {
            false
        }
    }

    private fun isNavigation(sbn: StatusBarNotification): Boolean {
        val navCategory = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P &&
            sbn.notification.category == Notification.CATEGORY_NAVIGATION
        return navCategory || (sbn.isOngoing && sbn.packageName in BlockedPackages.NAVIGATION)
    }

    companion object {
        @Volatile var navigating: Boolean = false
            private set
    }
}

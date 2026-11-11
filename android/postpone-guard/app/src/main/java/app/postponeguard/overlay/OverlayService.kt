package app.postponeguard.overlay

import android.app.KeyguardManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.provider.Settings
import android.util.Log
import android.view.WindowManager
import app.postponeguard.core.Decision
import app.postponeguard.core.Environment
import app.postponeguard.core.Item
import app.postponeguard.core.Items
import app.postponeguard.core.OverlayPolicy
import app.postponeguard.data.ItemStore
import app.postponeguard.env.CallState
import app.postponeguard.env.ForegroundApp
import app.postponeguard.env.NavNotificationListener
import app.postponeguard.ui.MainActivity
import java.time.LocalDate

/**
 * Foreground service that decides when to show the overlay.
 * - While the screen is on and unlocked it checks every minute.
 * - While the overlay is showing it re-checks the safety blockers every second
 *   (and immediately on a call-state change) and removes the overlay if one appears.
 */
class OverlayService : Service() {
    private val main = Handler(Looper.getMainLooper())
    private lateinit var store: ItemStore
    private lateinit var foreground: ForegroundApp
    private lateinit var calls: CallState
    private lateinit var wm: WindowManager
    private var overlay: OverlayView? = null

    private val check = object : Runnable {
        override fun run() {
            evaluate()
            main.removeCallbacks(this)
            if (screenUsable()) main.postDelayed(this, if (overlay != null) GUARD_MS else CHECK_MS)
        }
    }

    private val screen = object : BroadcastReceiver() {
        override fun onReceive(c: Context, i: Intent) {
            when (i.action) {
                Intent.ACTION_SCREEN_OFF -> { main.removeCallbacks(check); removeOverlay() }
                Intent.ACTION_USER_PRESENT, Intent.ACTION_SCREEN_ON -> main.post(check)
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        store = ItemStore(this)
        foreground = ForegroundApp(this)
        wm = getSystemService(WindowManager::class.java)
        calls = CallState(this, { main.post(it) }) { main.post { if (overlay != null) evaluate() } }
        startInForeground()
        calls.start()
        registerReceiver(screen, IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_USER_PRESENT)
        })
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_PREVIEW -> preview()
            ACTION_REFRESH -> { calls.stop(); calls.start(); main.post(check) }
            else -> main.post(check)
        }
        return START_STICKY
    }

    override fun onDestroy() {
        main.removeCallbacksAndMessages(null)
        unregisterReceiver(screen)
        calls.stop()
        removeOverlay()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun environment(): Environment = Environment(
        today = LocalDate.now(),
        nowMillis = System.currentTimeMillis(),
        lastShownAtMillis = store.lastShownAtMillis,
        userActive = screenUsable(),
        inCall = calls.inCall(),
        foregroundPackage = foreground.current(),
        defaultDialer = foreground.defaultDialer(),
        backgroundNavigation = NavNotificationListener.navigating,
    )

    private fun evaluate() {
        val env = environment()
        if (overlay != null) {
            OverlayPolicy.blocker(env)?.let { Log.i(TAG, "remove overlay: $it"); removeOverlay() }
            return
        }
        when (val d = OverlayPolicy.decide(store.load(), env)) {
            is Decision.Show -> showOverlay(d.item)
            is Decision.Hide -> Log.d(TAG, "no overlay: ${d.reason}")
        }
    }

    /** Debug preview from the app: ignores the day rule and the cap, never the safety blockers. */
    private fun preview() {
        if (overlay != null) return
        val item = Items.open(store.load()).firstOrNull() ?: return
        if (OverlayPolicy.blocker(environment()) == null) showOverlay(item, countsTowardCap = false)
    }

    private fun showOverlay(item: Item, countsTowardCap: Boolean = true) {
        if (!Settings.canDrawOverlays(this)) return
        val view = OverlayView(
            this, item,
            onDone = { store.update(item.id, Items::markDone); removeOverlay() },
            onSkip = { store.update(item.id) { Items.skipToday(it, LocalDate.now()) }; removeOverlay() },
            onEscape = { removeOverlay() },
        )
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.OPAQUE,
        )
        try {
            wm.addView(view, params)
        } catch (e: RuntimeException) {
            Log.w(TAG, "addView failed", e)
            return
        }
        overlay = view
        // The cap counts from when the overlay appears, so every way out is capped.
        if (countsTowardCap) store.lastShownAtMillis = System.currentTimeMillis()
        main.removeCallbacks(check)
        main.postDelayed(check, GUARD_MS)
    }

    private fun removeOverlay() {
        val v = overlay ?: return
        overlay = null
        try { wm.removeView(v) } catch (e: RuntimeException) { Log.w(TAG, "removeView failed", e) }
        if (screenUsable()) { main.removeCallbacks(check); main.postDelayed(check, CHECK_MS) }
    }

    private fun screenUsable(): Boolean =
        getSystemService(PowerManager::class.java).isInteractive &&
            !getSystemService(KeyguardManager::class.java).isKeyguardLocked

    private fun startInForeground() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel(CHANNEL, "Reminder service", NotificationManager.IMPORTANCE_MIN))
        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE,
        )
        val n = Notification.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_popup_reminder)
            .setContentTitle("Watching postponed tasks")
            .setContentIntent(open)
            .setOngoing(true)
            .build()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(NOTIFICATION_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(NOTIFICATION_ID, n)
        }
    }

    companion object {
        private const val TAG = "OverlayService"
        private const val CHANNEL = "service"
        private const val NOTIFICATION_ID = 1
        private const val CHECK_MS = 60_000L
        private const val GUARD_MS = 1_000L
        const val ACTION_PREVIEW = "app.postponeguard.PREVIEW"
        const val ACTION_REFRESH = "app.postponeguard.REFRESH"

        fun start(context: Context, action: String? = null) {
            context.startForegroundService(Intent(context, OverlayService::class.java).setAction(action))
        }
    }
}

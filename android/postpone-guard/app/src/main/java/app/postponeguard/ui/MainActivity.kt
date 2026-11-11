package app.postponeguard.ui

import android.Manifest
import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import app.postponeguard.core.Items
import app.postponeguard.data.ItemStore
import app.postponeguard.env.ForegroundApp
import app.postponeguard.env.NavNotificationListener
import app.postponeguard.overlay.OverlayService
import java.time.LocalDate

/** Item list, permission set-up and a preview button. Built in code to stay dependency-free. */
class MainActivity : Activity() {
    private lateinit var store: ItemStore
    private lateinit var root: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = ItemStore(this)
        root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(16), dp(16), dp(16)) }
        setContentView(ScrollView(this).apply { addView(root) })
    }

    override fun onResume() {
        super.onResume()
        render()
        OverlayService.start(this)
    }

    private fun render() {
        root.removeAllViews()
        section("Permissions")
        permission("Display over other apps", Settings.canDrawOverlays(this)) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
        }
        permission("Usage access (to see the app in front)", ForegroundApp(this).hasAccess()) {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }
        val runtime = buildList {
            add(Manifest.permission.READ_PHONE_STATE)
            if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
        }
        permission("Phone state and notifications", runtime.all(::granted)) {
            requestPermissions(runtime.toTypedArray(), 1)
        }
        permission("Optional: notification access (detects navigation in the background)", notificationAccess()) {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }

        section("Tasks")
        val input = EditText(this).apply { hint = "New task" }
        root.addView(input)
        root.addView(Button(this).apply {
            text = "Add"
            setOnClickListener {
                val t = input.text.toString().trim()
                if (t.isNotEmpty()) { store.add(t); render() }
            }
        })

        val today = LocalDate.now()
        Items.open(store.load()).forEach { item ->
            val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, dp(8), 0, dp(8)) }
            row.addView(TextView(this).apply {
                text = "${item.title}\npostponed ${item.postponedDays} day(s)" +
                    if (item.skippedOn == today) " · skipped today" else ""
            }, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
            row.addView(Button(this).apply {
                text = "Postpone"
                isEnabled = item.lastPostponedOn != today
                setOnClickListener { store.update(item.id) { Items.postpone(it, today) }; render() }
            })
            row.addView(Button(this).apply {
                text = "Done"
                setOnClickListener { store.update(item.id, Items::markDone); render() }
            })
            root.addView(row)
        }

        section("Test")
        root.addView(Button(this).apply {
            text = "Preview overlay (ignores day rule and cap)"
            setOnClickListener { OverlayService.start(this@MainActivity, OverlayService.ACTION_PREVIEW) }
        })
    }

    private fun section(title: String) {
        root.addView(TextView(this).apply {
            text = title
            textSize = 20f
            setPadding(0, dp(16), 0, dp(4))
        })
    }

    private fun permission(label: String, ok: Boolean, request: () -> Unit) {
        root.addView(Button(this).apply {
            text = (if (ok) "✓ " else "Grant: ") + label
            isEnabled = !ok
            textAlignment = View.TEXT_ALIGNMENT_VIEW_START
            setOnClickListener { request() }
        })
    }

    private fun granted(p: String) = checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED

    private fun notificationAccess(): Boolean {
        val flat = Settings.Secure.getString(contentResolver, "enabled_notification_listeners") ?: return false
        val me = ComponentName(this, NavNotificationListener::class.java).flattenToString()
        return flat.split(':').any { it == me }
    }

    @Deprecated("Deprecated in Java")
    override fun onRequestPermissionsResult(code: Int, permissions: Array<out String>, results: IntArray) {
        render()
        // Re-register the call listener now that the permission may exist.
        OverlayService.start(this, OverlayService.ACTION_REFRESH)
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
